"""Export metadata for a Parquet-based taxonomy source."""

import json
import logging
from datetime import datetime
from pathlib import Path

import polars as pl
from config import BUILD_DIRECTORY
from db import db_connection


logger = logging.getLogger("LifemapBuilder")


def export_metadata(source: str, roots: list[str], taxonomy_file: Path) -> None:
    output_directory = BUILD_DIRECTORY / source
    output_directory.mkdir(parents=True, exist_ok=True)

    taxonomy = pl.read_parquet(taxonomy_file, columns=["taxon_id", "scientific_name"])
    names = dict(taxonomy.iter_rows())

    metadata = {"update": datetime.now().strftime("%Y-%m-%d"), "species": {}}
    conn = db_connection()
    cur = conn.cursor()

    total = 0
    for root_id in roots:
        cur.execute(
            "select nbdesc from points_prod where taxid=%s and cladecenter is null",
            (root_id,),
        )
        result = cur.fetchone()
        number = result[0] if result is not None else 0
        metadata["species"][names.get(root_id, root_id)] = number
        total += number

    conn.close()
    metadata["species"]["total"] = total

    with (output_directory / "metadata.json").open("w") as file:
        json.dump(metadata, file)
