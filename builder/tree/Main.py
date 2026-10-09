import gc
import logging
import sys
from argparse import ArgumentParser
from pathlib import Path

import AdditionalInfo
import check_ranks
import db
import export_data
import export_metadata
import GetAllTilesCoord
import getTrees
import Traverse
from config import (
    BUILD_DIRECTORY,
    GENOMES_DIRECTORY,
)

# Init logging
log_path = BUILD_DIRECTORY / "builder.log"
logger = logging.getLogger("LifemapBuilder")
logger.handlers.clear()
fh = logging.FileHandler(log_path, mode="w")
ch = logging.StreamHandler(stream=sys.stdout)
# formatter = logging.Formatter("%(asctime)s   %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
# ch.setFormatter(formatter)
# fh.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)
logger.propagate = False


def lifemap_build(
    *,
    simplify: bool,
    skip_traversal: bool = False,
    skip_add_info: bool = False,
    skip_db: bool = False,
    skip_data: bool = False,
    disable_progress: bool = False,
) -> None:
    logger.info("-- Creating genomes directory if needed")
    Path(GENOMES_DIRECTORY).mkdir(exist_ok=True)
    logger.info("-- Done")

    ## get the tree and update database
    if skip_traversal:
        logger.info("--- Skipping tree traversal as requested ---")
    else:
        logger.info("-- CREATING DATABASE")
        logger.info("---- Updating NCBI database...")
        Traverse.updateDB()
        logger.info("---- Building NCBI tree...")
        tree = getTrees.getTheTrees()
        if simplify:
            tree = Traverse.simplify_tree(tree)
        logger.info("---- Doing Archaeal tree...")
        ndid = Traverse.traverse_tree(tree, groupnb="1", starti=1, disable_progress=disable_progress)
        logger.info("---- Done")
        logger.info(f"---- Doing Eukaryotic tree... start at id: {ndid}")
        ndid = Traverse.traverse_tree(tree, groupnb="2", starti=ndid, disable_progress=disable_progress)
        logger.info("---- Done")
        logger.info(f"---- Doing Bact tree... start at id: {ndid}")
        ndid = Traverse.traverse_tree(tree, groupnb="3", starti=ndid, disable_progress=disable_progress)
        logger.info("---- Done")
        del tree

    # Garbage collect
    gc.collect()

    if skip_db:
        logger.info("--- Skipping postgis operations as requested ---")
    else:
        logger.info("---- Initialize Postgis database ----")
        db.init_db()
        # Create postgis geometries
        logger.info("---- Create Postgis geometries ----")
        db.create_geometries()
        logger.info("---- Done")
        # Copy postgis data to production tables
        logger.info("-- Copy postgis data to production tables --")
        db.copy_db_to_prod()
        logger.info("-- Done --")
        # Create postgis indexes
        logger.info("-- Creating indexes... ")
        db.create_index()
        logger.info("-- Done")

    # Garbage collect
    gc.collect()

    ## Get additional info
    if skip_add_info:
        logger.info("--- Skipping additional info as requested ---")
    else:
        logger.info("-- Downloading genomes if needed...")
        AdditionalInfo.download_genomes()
        logger.info("-- Getting additional Archaeal info...")
        AdditionalInfo.add_info(nbgroup="1")
        logger.info("-- Done")
        logger.info("-- Getting additional Euka info...")
        AdditionalInfo.add_info(nbgroup="2")
        logger.info("-- Done")
        logger.info("-- Getting additional Bacter info...")
        AdditionalInfo.add_info(nbgroup="3")
        logger.info("-- Done")
        logger.info("-- Combining tree and additional features...")
        AdditionalInfo.merge_features()
        logger.info("-- Done")

    # Garbage collect
    gc.collect()

    ## Write whole data to Rdada file for use in R package LifemapR (among others)
    if skip_data:
        logger.info("--- Skipping data export as requested ---")
    else:
        logger.info("-- Exporting data to parquet...")
        export_data.clean_lmdata()
        export_data.export_lmdata()
        logger.info("-- Done ")

    # Garbage collect
    gc.collect()

    ## Get New coordinates for generating tiles
    logger.info("-- Get new tiles coordinates")
    GetAllTilesCoord.get_all_coords()
    logger.info("-- Done")

    # Export metadata to metadata.json
    logger.info("-- Export metadata.json")
    export_metadata.export_metadata()
    logger.info("-- Done")

    # Check for missing rank translations
    logger.info("-- Check for missing rank translations")
    check_ranks.check_ranks()
    logger.info("-- Done")


if __name__ == "__main__":
    parser = ArgumentParser(description="Perform all Lifemap tree analysis, cleaning previous data if any.")
    parser.add_argument(
        "--simplify",
        action="store_true",
        help="Should the tree be simplified by removing environmental and unidentified species?",
    )
    parser.add_argument("--skip-traversal", action="store_true", help="Skip tree building")
    parser.add_argument("--skip-add-info", action="store_true", help="Skip additional info")
    parser.add_argument("--skip-db", action="store_true", help="Skip postgis operations")
    parser.add_argument("--skip-data-export", action="store_true", help="Skip data export")
    parser.add_argument("--disable-progress", action="store_true", help="Disable progress bars")

    args = parser.parse_args()

    # Build or update tree
    lifemap_build(
        simplify=args.simplify,
        skip_traversal=args.skip_traversal,
        skip_add_info=args.skip_add_info,
        skip_db=args.skip_db,
        skip_data=args.skip_data_export,
        disable_progress=args.disable_progress,
    )
