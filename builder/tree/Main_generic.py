import gc
import logging
import sys
from argparse import ArgumentParser
from pathlib import Path

import AdditionalInfo_generic
import check_ranks
import db
import export_data_generic
import export_metadata_generic
import getTrees_generic
import Traverse_generic
from config import BUILD_DIRECTORY

# Init logging
log_path = BUILD_DIRECTORY / "builder.log"
logger = logging.getLogger("LifemapBuilder")
logger.handlers.clear()
fh = logging.FileHandler(log_path, mode="w")
ch = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(ch)
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)
logger.propagate = False


TAXONOMY_DATASETS = Path(__file__).resolve().parents[2] / "data" / "taxonomy_datasets"


def lifemap_build(
    *,
    source: str,
    roots: list[str],
    simplify: bool,
    skip_traversal: bool = False,
    skip_add_info: bool = False,
    skip_data: bool = False,
    disable_progress: bool = False,
) -> None:
    source_directory = TAXONOMY_DATASETS / source
    formatted_directory = source_directory / "formatted_data"
    taxonomy_file = formatted_directory / "taxonomy.parquet"
    names_file = formatted_directory / "taxon_vernacular_names.parquet"
    info_file = formatted_directory / "taxon_info.parquet"

    logger.info("-- CREATING DATABASE")
    logger.info("---- Initialize Postgis database ----")
    db.init_db()

    if skip_traversal:
        logger.info("--- Skipping tree traversal as requested ---")
    else:
        logger.info(f"---- Building {source} tree...")
        tree = getTrees_generic.getTheTreesFromParquet(taxonomy_file, names_file)
        if simplify:
            tree = Traverse_generic.simplify_tree(tree)
        Traverse_generic.traverse_tree(
            tree,
            roots=roots,
            source=source,
            starti=1,
            disable_progress=disable_progress,
        )
        del tree

    # Garbage collect
    gc.collect()

    # Create postgis geometries
    logger.info("---- Create Postgis geometries ----")
    db.create_geometries()
    logger.info("---- Done ----")
    # Copy postgis data to production tables
    logger.info("-- Copy postgis data to production tables --")
    db.copy_db_to_prod()
    logger.info("-- Done --")
    # Create postgis indexes
    logger.info("-- Creating indexes... ")
    db.create_index()
    logger.info("-- Done")

    # Get additional info
    if skip_add_info:
        logger.info("--- Skipping additional info as requested ---")
    else:
        logger.info("-- Creating additional information file...")
        AdditionalInfo_generic.prepare_additional_info(source, info_file)
        logger.info("-- Done")

    # Garbage collect
    gc.collect()

    ## Write whole data to R data file for use in R package LifemapR (among others)
    if skip_data:
        logger.info("--- Skipping data export as requested ---")
    else:
        logger.info("-- Exporting data to parquet...")
        export_data_generic.export_lmdata(source, info_file)
        logger.info("-- Done ")

    # Export metadata to metadata.json
    logger.info("-- Export metadata.json")
    export_metadata_generic.export_metadata(source, roots, taxonomy_file)
    logger.info("-- Done")

    # Check for missing rank translations
    logger.info("-- Check for missing rank translations")
    check_ranks.check_ranks()
    logger.info("-- Done")


if __name__ == "__main__":
    parser = ArgumentParser(description="Perform all Lifemap tree analysis, cleaning previous data if any.")
    parser.add_argument("--source", required=True, help="Taxonomy source to use")
    parser.add_argument(
        "--roots",
        nargs="+",
        required=True,
        help="Taxon IDs of the roots to display",
    )
    parser.add_argument(
        "--simplify",
        action="store_true",
        help="Should the tree be simplified by removing environmental and unidentified species?",
    )
    parser.add_argument("--skip-traversal", action="store_true", help="Skip tree traversal")
    parser.add_argument("--skip-add-info", action="store_true", help="Skip additional info")
    parser.add_argument("--skip-data-export", action="store_true", help="Skip data export")
    parser.add_argument("--disable-progress", action="store_true", help="Disable progress bars")

    args = parser.parse_args()

    # Build or update tree
    lifemap_build(
        source=args.source,
        roots=args.roots,
        simplify=args.simplify,
        skip_traversal=args.skip_traversal,
        skip_add_info=args.skip_add_info,
        skip_data=args.skip_data_export,
        disable_progress=args.disable_progress,
    )
