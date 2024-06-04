import json
import logging
import sys
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from typing import Literal

import AdditionalInfo
import CombineJsons
import CreateIndex
import GetAllTilesCoord
import PrepareRdata
import Traverse_To_Pgsql_2
from config import (
    BUILD_DIRECTORY,
    GENOMES_DIRECTORY,
    TAXO_DIRECTORY,
)

# Init logging
log_path = BUILD_DIRECTORY / "builder.log"
logger = logging.getLogger("LifemapBuilder")
fh = logging.FileHandler(log_path, mode="w")
ch = logging.StreamHandler(stream=sys.stdout)
# formatter = logging.Formatter("%(asctime)s   %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
# ch.setFormatter(formatter)
# fh.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)


def lifemap_build(
    lang: Literal["EN", "FR"],
    simplify: bool,
    skip_traversal: bool = False,
    skip_add_info: bool = False,
    skip_merge_jsons: bool = False,
    skip_rdata: bool = False,
    skip_index: bool = False,
) -> None:

    logger.info("-- Creating genomes directory if needed")
    Path(GENOMES_DIRECTORY).mkdir(exist_ok=True)
    logger.info("-- Done")

    ## get the tree and update database
    if skip_traversal:
        logger.info("--- Skipping tree traversal as requested ---")
    else:
        logger.info("-- CREATING DATABASE")
        logger.info("---- Doing Archaeal tree...")
        ndid = Traverse_To_Pgsql_2.traverse_tree(
            groupnb="1", starti=1, simplify=simplify, lang=lang, updatedb=True
        )
        logger.info("---- Done")
        logger.info("---- Doing Eukaryotic tree... start at id: %s" % ndid)
        ndid = Traverse_To_Pgsql_2.traverse_tree(
            groupnb="2", starti=ndid, simplify=simplify, lang=lang, updatedb=False
        )
        logger.info("---- Done")
        logger.info("---- Doing Bact tree... start at id:%s " % ndid)
        ndid = Traverse_To_Pgsql_2.traverse_tree(
            groupnb="3", starti=ndid, simplify=simplify, lang=lang, updatedb=False
        )
        logger.info("---- Done")

    ## Get additional info from NCBI
    if skip_add_info:
        logger.info("--- Skipping additional info as requested ---")
    else:
        logger.info("-- Downloading genomes if needed...")
        AdditionalInfo.download_genomes()
        logger.info("-- Getting additional Archaeal info...")
        AdditionalInfo.add_info(groupnb="1")
        logger.info("-- Getting additional Euka info...")
        AdditionalInfo.add_info(groupnb="2")
        logger.info("-- Getting additional Bacter info...")
        AdditionalInfo.add_info(groupnb="3")
        logger.info("-- Done")

    ##2.1. Get FULL info from NCBI (new sept 2019)
    # os.system('python StoreWholeNcbiInSolr.py')
    # logger.info '  ...Done'

    ## Merge Additionaljson and TreeFeatures json
    if skip_merge_jsons:
        logger.info("--- Skipping JSONs merging as requested ---")
    else:
        logger.info("---- Merging jsons...")
        CombineJsons.merge_all()
        logger.info("---- Done ")

    ## Write whole data to Rdada file for use in R package LifemapR (among others)
    if skip_rdata:
        logger.info("--- Skipping Rdata export as requested ---")
    else:
        logger.info("-- Converting json to Rdata for light data sharing...")
        PrepareRdata.create_rdata()
        logger.info("-- Done ")

    ## Create postgis index
    if skip_index:
        logger.info("--- Skipping index creation as requested ---")
    else:
        logger.info("-- Creating index... ")
        CreateIndex.create_index()
        logger.info("-- Done")

    ## Get New coordinates for generating tiles
    logger.info("-- Get new tiles coordinates")
    GetAllTilesCoord.get_all_coords()
    logger.info("-- Done")

    #  Get and copy date of update to /var/www/html
    logger.info("-- Update date-update.json")
    date_update = (TAXO_DIRECTORY / "taxdump.tar.gz").stat().st_mtime
    date_update = datetime.fromtimestamp(date_update)
    date_update = {"update": date_update.strftime("%Y-%m-%d")}
    # Create the directory if it doesn't exist
    Path(BUILD_DIRECTORY).mkdir(exist_ok=True)
    date_update_file = BUILD_DIRECTORY / "date-update.json"
    with open(date_update_file, "w") as f:
        json.dump(date_update, f)
    logger.info("-- Done")


if __name__ == "__main__":

    parser = ArgumentParser(
        description="Perform all Lifemap tree analysis cleaning previous data if any."
    )
    parser.add_argument(
        "--lang",
        action="store",
        default="EN",
        help="Language chosen. FR for french, EN (default) for english",
        choices=["EN", "FR"],
    )
    parser.add_argument(
        "--simplify",
        action="store_true",
        help="Should the tree be simplified by removing environmental and unindentified species?",
    )
    parser.add_argument(
        "--skip-traversal", action="store_true", help="Skip tree building"
    )
    parser.add_argument(
        "--skip-add-info", action="store_true", help="Skip additional info"
    )
    parser.add_argument(
        "--skip-merge-jsons", action="store_true", help="Skip JSONs merging"
    )
    parser.add_argument("--skip-rdata", action="store_true", help="Skip Rdata export")
    parser.add_argument("--skip-index", action="store_true", help="Skip index creation")

    args = parser.parse_args()

    # Build or update tree
    lifemap_build(
        lang=args.lang,
        simplify=args.simplify,
        skip_traversal=args.skip_traversal,
        skip_add_info=args.skip_add_info,
        skip_merge_jsons=args.skip_merge_jsons,
        skip_rdata=args.skip_rdata,
        skip_index=args.skip_index,
    )
