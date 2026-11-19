"""Convert a WoRMS Darwin Core archive into the common Parquet files."""

import argparse
import csv
import io
import sys
import zipfile
from pathlib import Path

import polars as pl


csv.field_size_limit(sys.maxsize)


def open_table(archive: zipfile.ZipFile, filename: str) -> csv.DictReader:
    archive_filename = next(
        name for name in archive.namelist() if name == filename or name.endswith(f"/{filename}")
    )
    file = archive.open(archive_filename)
    text_file = io.TextIOWrapper(file, encoding="utf-8")
    return csv.DictReader(text_file, delimiter="\t")


def short_id(taxon_id: str) -> str:
    if taxon_id:
        return taxon_id.rsplit(":", 1)[-1]
    return ""


def read_taxonomy(archive: zipfile.ZipFile) -> dict[str, dict]:
    rows = {}

    for row in open_table(archive, "taxon.txt"):
        taxon_id = short_id(row["taxonID"])
        rows[taxon_id] = {
            "taxon_id": taxon_id,
            "parent_taxon_id": short_id(row["parentNameUsageID"]),
            "scientific_name": row["scientificName"],
            "rank": row["taxonRank"].lower(),
            "authority": row["scientificNameAuthorship"],
            "status": row["taxonomicStatus"],
            "accepted_taxon_id": short_id(row["acceptedNameUsageID"]),
        }

    kept_ids = set()
    for taxon_id, row in rows.items():
        if (
            row["status"] == "accepted"
            or not row["accepted_taxon_id"]
            or row["accepted_taxon_id"] == taxon_id
        ):
            kept_ids.add(taxon_id)

    taxa = {}
    for taxon_id in kept_ids:
        row = rows[taxon_id]
        taxa[taxon_id] = {
            "taxon_id": taxon_id,
            "parent_taxon_id": find_kept_parent(row["parent_taxon_id"], rows, kept_ids),
            "scientific_name": row["scientific_name"],
            "rank": row["rank"],
            "authority": row["authority"],
            "synonyms": [],
        }

    for taxon_id, row in rows.items():
        if taxon_id in kept_ids:
            continue

        accepted_taxon_id = find_kept_parent(row["accepted_taxon_id"], rows, kept_ids)
        if accepted_taxon_id in taxa:
            taxa[accepted_taxon_id]["synonyms"].append(row["scientific_name"])

    check_tree(taxa)

    return taxa


def find_kept_parent(parent_id: str, rows: dict[str, dict], kept_ids: set[str]) -> str:
    while parent_id and parent_id not in kept_ids:
        accepted_id = rows[parent_id]["accepted_taxon_id"]
        if accepted_id and accepted_id != parent_id:
            parent_id = accepted_id
        else:
            parent_id = rows[parent_id]["parent_taxon_id"]

    return parent_id


def check_tree(taxa: dict[str, dict]) -> None:
    roots = [taxon_id for taxon_id, row in taxa.items() if not row["parent_taxon_id"]]
    if len(roots) != 1:
        raise ValueError(f"Expected one root, found {len(roots)}")

    for taxon_id, row in taxa.items():
        parent = row["parent_taxon_id"]
        if parent and parent not in taxa:
            raise ValueError(f"Parent {parent} of taxon {taxon_id} is missing")

        seen = set()
        current = taxon_id
        while current:
            if current in seen:
                raise ValueError(f"Cycle found at taxon {current}")
            seen.add(current)
            current = taxa[current]["parent_taxon_id"]


def create_info(taxa: dict[str, dict]) -> pl.DataFrame:
    parents = {taxon_id: row["parent_taxon_id"] for taxon_id, row in taxa.items()}
    rows = []

    for taxon_id in taxa:
        parent = parents[taxon_id]
        ascend = []

        while parent != taxon_id and parent in parents:
            ascend.append(parent)
            parent = parents[parent]

        if not ascend or ascend[-1] != "0":
            ascend.append("0")
        rows.append({"taxon_id": taxon_id, "ascend": ascend})

    return pl.DataFrame(rows)


def prepare_worms(source_directory: Path) -> None:
    downloads_directory = source_directory / "downloads"
    output_directory = source_directory / "formatted_data"
    source_directory.mkdir(parents=True, exist_ok=True)
    downloads_directory.mkdir(parents=True, exist_ok=True)
    output_directory.mkdir(parents=True, exist_ok=True)
    input_file = next(downloads_directory.glob("*.zip"))

    print("Reading WoRMS taxonomy...")
    with zipfile.ZipFile(input_file) as archive:
        taxa = read_taxonomy(archive)

    print("Writing taxonomy.parquet...")
    taxonomy = pl.DataFrame(list(taxa.values())).with_columns(
        pl.col("synonyms").cast(pl.List(pl.String))
    )
    taxonomy.write_parquet(output_directory / "taxonomy.parquet")

    print("Writing empty taxon_vernacular_names.parquet...")
    names = pl.DataFrame(
        schema={
            "taxon_id": pl.String,
            "language": pl.String,
            "name": pl.String,
        }
    )
    names.write_parquet(output_directory / "taxon_vernacular_names.parquet")

    print("Computing ascend and writing taxon_info.parquet...")
    info_file = output_directory / "taxon_info.parquet"
    create_info(taxa).write_parquet(info_file)
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_directory", type=Path)
    args = parser.parse_args()
    prepare_worms(args.source_directory)
