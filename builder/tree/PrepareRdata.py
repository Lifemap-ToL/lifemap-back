#!/usr/bin/python3

import subprocess
from pathlib import Path

from config import LMDATA_DIRECTORY, BUILD_DIRECTORY


def create_rdata():

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

    # Execute the R script
    script_dir = Path(__file__).parent.absolute()
    script_file = script_dir / "ConvertAndCompress.R"
    try:
        subprocess.run(["Rscript", str(script_file), BUILD_DIRECTORY])
    except Exception as e:
        raise RuntimeError(f"Error executing R script: {e}")

    # Move the lmdata.Rdata file to the new location
    source_file = "lmdata.Rdata"
    dest_file = LMDATA_DIRECTORY / source_file

    try:
        Path(source_file).rename(dest_file)
        print(f"File {source_file} moved to {dest_file}")
    except Exception as e:
        raise RuntimeError(f"Error moving {source_file} to {dest_file}: {e}")
