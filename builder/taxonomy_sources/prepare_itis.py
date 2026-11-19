"""Convert an ITIS SQLite export into the common Parquet files."""

import argparse
import sqlite3
import tempfile
import zipfile
from pathlib import Path

import polars as pl


ROOT_ID = "0"

LANGUAGES = {
    "english": "en",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "greek": "el",
}


def find_database(archive: zipfile.ZipFile) -> str:
    for filename in archive.namelist():
        if filename.endswith("ITIS.sqlite"):
            return filename

    raise FileNotFoundError("ITIS.sqlite was not found in the zip file")


def read_taxonomy(database: sqlite3.Connection) -> tuple[list[dict], dict, dict]:
    taxonomy = {}
    info = {}

    query = """
        select h.TSN, h.Parent_TSN, tu.complete_name, tu.taxon_author_id,
               tu.kingdom_id, tu.rank_id, tu.name_usage, t.rank_name,
               a.taxon_author
        from hierarchy h
        join taxonomic_units tu on tu.tsn = h.TSN
        left join taxon_unit_types t
            on t.kingdom_id = tu.kingdom_id and t.rank_id = tu.rank_id
        left join taxon_authors_lkp a
            on a.taxon_author_id = tu.taxon_author_id
            and a.kingdom_id = tu.kingdom_id
    """

    for row in database.execute(query):
        taxon_id = str(row[0])
        taxonomy[taxon_id] = {
            "taxon_id": taxon_id,
            "parent_taxon_id": str(row[1]),
            "scientific_name": row[2],
            "rank": row[7] or "",
            "authority": row[8] or "",
            "synonyms": [],
        }
        info[taxon_id] = {
            "taxon_id": taxon_id,
            "status": row[6],
        }

    taxonomy[ROOT_ID] = {
        "taxon_id": ROOT_ID,
        "parent_taxon_id": "",
        "scientific_name": "root",
        "rank": "root",
        "authority": "",
        "synonyms": [],
    }
    info[ROOT_ID] = {"taxon_id": ROOT_ID, "status": "root"}

    return list(taxonomy.values()), info, taxonomy


def read_synonyms(database: sqlite3.Connection, taxonomy: dict) -> None:
    query = """
        select sl.tsn_accepted, tu.complete_name
        from synonym_links sl
        join taxonomic_units tu on tu.tsn = sl.tsn
    """

    for accepted_id, name in database.execute(query):
        accepted_id = str(accepted_id)
        if accepted_id in taxonomy and name:
            taxonomy[accepted_id]["synonyms"].append(name)


def read_vernacular_names(
    database: sqlite3.Connection, taxonomy: dict
) -> list[dict]:
    names = []

    for taxon_id, name, language in database.execute(
        "select tsn, vernacular_name, language from vernaculars"
    ):
        taxon_id = str(taxon_id)
        language = LANGUAGES.get(language.lower())

        if taxon_id in taxonomy and language and name:
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


def prepare_itis(source_directory: Path) -> None:
    downloads_directory = source_directory / "downloads"
    output_directory = source_directory / "formatted_data"
    source_directory.mkdir(parents=True, exist_ok=True)
    downloads_directory.mkdir(parents=True, exist_ok=True)
    output_directory.mkdir(parents=True, exist_ok=True)
    input_file = next(downloads_directory.glob("*.zip"))

    print("Reading ITIS taxonomy...")
    with tempfile.TemporaryDirectory() as temporary_directory:
        with zipfile.ZipFile(input_file) as archive:
            database_file = archive.extract(
                find_database(archive), temporary_directory
            )

        database = sqlite3.connect(database_file)
        taxonomy_rows, info, taxonomy = read_taxonomy(database)
        read_synonyms(database, taxonomy)
        names_rows = read_vernacular_names(database, taxonomy)
        database.close()

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
    prepare_itis(args.source_directory)
