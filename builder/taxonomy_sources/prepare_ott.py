"""Convert an OpenTree of Life taxonomy export into Parquet files."""

import argparse
import csv
import io
import tarfile
from pathlib import Path

import polars as pl


def open_table(archive: tarfile.TarFile, filename: str) -> csv.DictReader:
    for member in archive.getmembers():
        if member.name.endswith(filename):
            file = archive.extractfile(member)
            text_file = io.TextIOWrapper(file, encoding="utf-8")
            return csv.DictReader(text_file, delimiter="\t")

    raise FileNotFoundError(f"{filename} was not found in the archive")


def value(row: dict, column: str) -> str:
    return row[column].strip()


def read_taxonomy(archive: tarfile.TarFile) -> tuple[list[dict], dict]:
    taxonomy = {}
    info = {}

    print("Reading OTT taxonomy...")
    for row in open_table(archive, "taxonomy.tsv"):
        taxon_id = value(row, "uid")
        taxonomy[taxon_id] = {
            "taxon_id": taxon_id,
            "parent_taxon_id": value(row, "parent_uid"),
            "scientific_name": value(row, "name"),
            "rank": value(row, "rank"),
            "authority": "",
            "synonyms": [],
        }
        info[taxon_id] = {
            "taxon_id": taxon_id,
            "sourceinfo": value(row, "sourceinfo"),
            "uniqname": value(row, "uniqname"),
            "flags": value(row, "flags"),
        }

    return list(taxonomy.values()), info, taxonomy


def read_synonyms(archive: tarfile.TarFile, taxonomy: dict) -> None:
    print("Reading OTT synonyms...")
    for row in open_table(archive, "synonyms.tsv"):
        taxon_id = value(row, "uid")
        name = value(row, "name")

        if taxon_id in taxonomy and name:
            taxonomy[taxon_id]["synonyms"].append(name)


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


def prepare_ott(source_directory: Path) -> None:
    downloads_directory = source_directory / "downloads"
    output_directory = source_directory / "formatted_data"
    source_directory.mkdir(parents=True, exist_ok=True)
    downloads_directory.mkdir(parents=True, exist_ok=True)
    output_directory.mkdir(parents=True, exist_ok=True)
    input_file = next(downloads_directory.glob("*.tgz"))

    with tarfile.open(input_file) as archive:
        taxonomy_rows, info, taxonomy = read_taxonomy(archive)
        read_synonyms(archive, taxonomy)

    print("Writing taxonomy.parquet...")
    pl.DataFrame(taxonomy_rows).with_columns(
        pl.col("synonyms").cast(pl.List(pl.String))
    ).write_parquet(output_directory / "taxonomy.parquet")

    print("Writing empty taxon_vernacular_names.parquet...")
    names = pl.DataFrame(
        schema={
            "taxon_id": pl.String,
            "language": pl.String,
            "name": pl.String,
        }
    )
    names.write_parquet(output_directory / "taxon_vernacular_names.parquet")

    info_file = output_directory / "taxon_info.parquet"
    print("Writing taxon_info.parquet...")
    pl.DataFrame(list(info.values())).write_parquet(info_file)

    print("Computing ascend...")
    add_ascend(output_directory / "taxonomy.parquet", info_file)
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_directory", type=Path)
    args = parser.parse_args()
    prepare_ott(args.source_directory)
