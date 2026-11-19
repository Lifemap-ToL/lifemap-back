"""Convert a GBIF Backbone export into the common Parquet files."""

import argparse
import csv
import io
import zipfile
from pathlib import Path

import polars as pl


ROOT_ID = "-1"

LANGUAGES = {
    "eng": "en",
    "spa": "es",
    "fra": "fr",
    "deu": "de",
    "ell": "el",
    "por": "pt",
    "ita": "it",
}


def open_table(archive: zipfile.ZipFile, filename: str) -> csv.DictReader:
    file = archive.open(filename)
    text_file = io.TextIOWrapper(file, encoding="utf-8")
    return csv.DictReader(text_file, delimiter="\t")


def read_taxa(archive: zipfile.ZipFile) -> tuple[list[dict], dict, list[dict]]:
    taxonomy = {}
    info = {}

    print("Reading GBIF taxonomy...")
    for row in open_table(archive, "Taxon.tsv"):
        status = row["taxonomicStatus"]
        taxon_id = row["taxonID"]
        name = row["scientificName"]

        if status not in ["accepted", "doubtful"] or not name:
            continue

        taxonomy[taxon_id] = {
            "taxon_id": taxon_id,
            "parent_taxon_id": row["parentNameUsageID"] or ROOT_ID,
            "scientific_name": name,
            "rank": row["taxonRank"],
            "authority": row["scientificNameAuthorship"],
            "synonyms": [],
        }
        info[taxon_id] = {
            "taxon_id": taxon_id,
            "status": status,
            "kingdom": row["kingdom"],
            "phylum": row["phylum"],
            "class": row["class"],
            "order": row["order"],
            "family": row["family"],
            "genus": row["genus"],
        }

    print("Reading GBIF synonyms...")
    for row in open_table(archive, "Taxon.tsv"):
        accepted_id = row["acceptedNameUsageID"]
        name = row["scientificName"]

        if accepted_id in taxonomy and name and accepted_id != row["taxonID"]:
            taxonomy[accepted_id]["synonyms"].append(name)

    root = {
        "taxon_id": ROOT_ID,
        "parent_taxon_id": "",
        "scientific_name": "root",
        "rank": "root",
        "authority": "",
        "synonyms": [],
    }
    taxonomy[ROOT_ID] = root
    info[ROOT_ID] = {
        "taxon_id": ROOT_ID,
        "status": "accepted",
        "kingdom": "",
        "phylum": "",
        "class": "",
        "order": "",
        "family": "",
        "genus": "",
    }

    return list(taxonomy.values()), info, taxonomy


def read_vernacular_names(archive: zipfile.ZipFile, taxonomy: dict) -> list[dict]:
    names = []

    print("Reading GBIF vernacular names...")
    for row in open_table(archive, "VernacularName.tsv"):
        taxon_id = row["taxonID"]
        name = row["vernacularName"]
        language = LANGUAGES.get(row["language"], row["language"])

        if taxon_id in taxonomy and name and language:
            names.append(
                {
                    "taxon_id": taxon_id,
                    "language": language,
                    "name": name,
                }
            )

    return names


def add_ascend(taxonomy_file: Path, info_file: Path) -> None:
    taxonomy = pl.read_parquet(taxonomy_file, columns=["taxon_id", "parent_taxon_id"])
    parents = dict(taxonomy.iter_rows())
    info = pl.read_parquet(info_file)

    def get_ancestors(taxon_id: str) -> list[str]:
        parent = parents[taxon_id]
        ascend = []

        while parent and parent != taxon_id:
            ascend.append(parent)
            parent = parents[parent]

        if not ascend or ascend[-1] != "0":
            ascend.append("0")
        return ascend

    info = info.with_columns(
        pl.col("taxon_id")
        .map_elements(get_ancestors, return_dtype=pl.List(pl.String))
        .alias("ascend")
    )
    info.write_parquet(info_file)


def prepare_gbif(source_directory: Path) -> None:
    downloads_directory = source_directory / "downloads"
    output_directory = source_directory / "formatted_data"
    source_directory.mkdir(parents=True, exist_ok=True)
    downloads_directory.mkdir(parents=True, exist_ok=True)
    output_directory.mkdir(parents=True, exist_ok=True)
    input_file = next(downloads_directory.glob("*.zip"))

    with zipfile.ZipFile(input_file) as archive:
        taxonomy_rows, info, taxonomy = read_taxa(archive)
        names_rows = read_vernacular_names(archive, taxonomy)

    print("Writing taxonomy.parquet...")
    pl.DataFrame(taxonomy_rows).with_columns(
        pl.col("synonyms").cast(pl.List(pl.String))
    ).write_parquet(output_directory / "taxonomy.parquet")

    print("Writing taxon_vernacular_names.parquet...")
    pl.DataFrame(names_rows).unique().write_parquet(
        output_directory / "taxon_vernacular_names.parquet"
    )

    print("Writing taxon_info.parquet...")
    pl.DataFrame(list(info.values())).write_parquet(
        output_directory / "taxon_info.parquet"
    )

    print("Computing ascend...")
    info_file = output_directory / "taxon_info.parquet"
    add_ascend(output_directory / "taxonomy.parquet", info_file)
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_directory", type=Path)
    args = parser.parse_args()
    prepare_gbif(args.source_directory)
