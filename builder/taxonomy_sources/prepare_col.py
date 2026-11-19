"""Convert a Catalogue of Life EX export into the common Parquet files."""

import argparse
import csv
import io
import sys
import zipfile
from pathlib import Path

import polars as pl


csv.field_size_limit(sys.maxsize)


LANGUAGES = {
    "eng": "en",
    "spa": "es",
    "fra": "fr",
    "deu": "de",
    "ell": "el",
}


def open_table(archive: zipfile.ZipFile, filename: str) -> csv.DictReader:
    file = archive.open(filename)
    text_file = io.TextIOWrapper(file, encoding="utf-8")
    return csv.DictReader(text_file, delimiter="\t")


def read_name_usage(archive: zipfile.ZipFile) -> tuple[list[dict], list[dict]]:
    taxonomy_rows = []
    info_rows = []

    for row in open_table(archive, "NameUsage.tsv"):
        if row["col:status"] not in ["accepted", "provisionally accepted"]:
            continue

        taxon_id = row["col:ID"]
        taxonomy_rows.append(
            {
                "taxon_id": taxon_id,
                "parent_taxon_id": row["col:parentID"],
                "scientific_name": row["col:scientificName"],
                "rank": row["col:rank"],
                "authority": row["col:authorship"],
                "synonyms": [],
            }
        )
        info_rows.append(
            {
                "taxon_id": taxon_id,
                "status": row["col:status"],
                "extinct": row["col:extinct"],
                "environment": row["col:environment"],
                "temporal_range_start": row["col:temporalRangeStart"],
                "temporal_range_end": row["col:temporalRangeEnd"],
            }
        )

    return taxonomy_rows, info_rows


def read_vernacular_names(archive: zipfile.ZipFile) -> list[dict]:
    rows = []

    for row in open_table(archive, "VernacularName.tsv"):
        language = LANGUAGES.get(row["col:language"])
        name = row["col:name"]

        if language and name:
            rows.append(
                {
                    "taxon_id": row["col:taxonID"],
                    "language": language,
                    "name": name,
                }
            )

    return rows


def add_ascend(taxonomy_file: Path, info_file: Path) -> None:
    taxonomy = pl.read_parquet(taxonomy_file, columns=["taxon_id", "parent_taxon_id"])
    parents = dict(taxonomy.iter_rows())
    info = pl.read_parquet(info_file)

    def get_ancestors(taxon_id: str) -> list[str]:
        parent = parents[taxon_id]
        ascend = []

        while parent != taxon_id and parent in parents:
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


def prepare_col(source_directory: Path) -> None:
    downloads_directory = source_directory / "downloads"
    output_directory = source_directory / "formatted_data"
    source_directory.mkdir(parents=True, exist_ok=True)
    downloads_directory.mkdir(parents=True, exist_ok=True)
    output_directory.mkdir(parents=True, exist_ok=True)
    input_file = next(downloads_directory.glob("*.zip"))

    print("Reading Catalogue of Life taxonomy and vernacular names...")
    with zipfile.ZipFile(input_file) as archive:
        taxonomy_rows, info_rows = read_name_usage(archive)
        names_rows = read_vernacular_names(archive)

    taxonomy_file = output_directory / "taxonomy.parquet"
    info_file = output_directory / "taxon_info.parquet"

    print("Writing taxonomy.parquet...")
    pl.DataFrame(taxonomy_rows).with_columns(
        pl.col("synonyms").cast(pl.List(pl.String))
    ).write_parquet(taxonomy_file)
    print("Writing taxon_vernacular_names.parquet...")
    pl.DataFrame(names_rows).unique().write_parquet(
        output_directory / "taxon_vernacular_names.parquet"
    )
    print("Writing taxon_info.parquet...")
    pl.DataFrame(info_rows).write_parquet(info_file)

    del taxonomy_rows, names_rows, info_rows
    print("Computing ascend...")
    add_ascend(taxonomy_file, info_file)
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_directory", type=Path)
    args = parser.parse_args()
    prepare_col(args.source_directory)
