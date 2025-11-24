#!/usr/bin/python3

import json
import logging
from datetime import datetime
from pathlib import Path

from config import BUILD_DIRECTORY, TAXO_DIRECTORY
from db import db_connection

logger = logging.getLogger("LifemapBuilder")


def export_metadata() -> None:
    meta = {}

    # Date of NCBI data
    logger.info("  Getting NCBI data date...")
    date_update = (TAXO_DIRECTORY / "taxdump.tar.gz").stat().st_mtime
    date_update = datetime.fromtimestamp(date_update)
    meta["update"] = date_update.strftime("%Y-%m-%d")

    logger.info("  Getting number of species...")
    meta["species"] = {}
    # Connect to postgis
    conn = db_connection()
    cur = conn.cursor()

    # Number of leaves (species) for archaea
    query = "select nbdesc from points where taxid='2157' and cladecenter is null;"
    cur.execute(query)
    res = cur.fetchone()
    n1 = res[0] if res is not None else 0
    # Number of leaves (species) for eukaryotes
    query = "select nbdesc from points where taxid='2759' and cladecenter is null;"
    cur.execute(query)
    res = cur.fetchone()
    n2 = res[0] if res is not None else 0
    # Number of leaves (species) for bacteria
    query = "select nbdesc from points where taxid='2' and cladecenter is null;"
    cur.execute(query)
    res = cur.fetchone()
    n3 = res[0] if res is not None else 0

    conn.close()
    meta["species"]["archaea"] = n1
    meta["species"]["eukaryotes"] = n2
    meta["species"]["bacteria"] = n3
    meta["species"]["total"] = n1 + n2 + n3

    logger.info("  Writing metadata.json...")
    # Create the directory if it doesn't exist
    Path(BUILD_DIRECTORY).mkdir(exist_ok=True)
    metadata_file = BUILD_DIRECTORY / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(meta, f)
