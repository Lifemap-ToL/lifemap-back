#!/usr/bin/python3

import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from config import BUILD_DIRECTORY, LMDATA_DIRECTORY

logger = logging.getLogger("LifemapBuilder")


def clean_lmdata() -> None:

    logger.info(" Cleaning lmdata directory...")

    # Create the directory if it doesn't exist
    Path(LMDATA_DIRECTORY).mkdir(exist_ok=True)

    # Remove any files in the directory
    # Iterate over all files in the directory and delete them
    for file_path in LMDATA_DIRECTORY.glob("*"):
        if file_path.is_file():
            try:
                file_path.unlink()
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")


def export_lmdata() -> None:

    logger.info(" Creating timestamp file...")
    # Get the current datetime
    now = datetime.now()
    # Format the datetime as a string in the desired format
    now_str = now.strftime("%Y%m%d%H%M")

    with open(LMDATA_DIRECTORY / "timestamp.txt", "w") as f:
        f.write(now_str)

    logger.info(" Copying parquet file to lmdata directory...")

    # Copy parquet file to lmdata directory
    features_file = BUILD_DIRECTORY / "TreeFeaturesComplete.parquet"
    dest_file = LMDATA_DIRECTORY / "lmdata.parquet"
    try:
        shutil.copyfile(features_file, dest_file)
    except Exception as e:
        raise RuntimeError(f"Error copying {features_file} to {dest_file}: {e}")

    logger.info(" Converting parquet file to Rdata file...")
    # Execute the R conversion script
    script_dir = Path(__file__).parent.absolute()
    script_file = script_dir / "Convert2Rdata.R"
    try:
        subprocess.run(["Rscript", str(script_file), LMDATA_DIRECTORY])
    except Exception as e:
        raise RuntimeError(f"Error executing R script: {e}")
