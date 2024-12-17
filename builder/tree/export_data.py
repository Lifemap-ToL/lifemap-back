#!/usr/bin/python3

import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import polars as pl
from config import BUILD_DIRECTORY, LMDATA_DIRECTORY

logger = logging.getLogger("LifemapBuilder")

LUCA = {"lat": -4.226497, "lon": 0}


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


def convert_features(lm: pl.DataFrame) -> pl.DataFrame:
    # Add root
    lm = pl.concat(
        [
            lm,
            pl.DataFrame(
                [
                    {
                        "taxid": 0,
                        "sci_name": "Luca",
                        "zoom": 5,
                        "lat": LUCA["lat"],
                        "lon": LUCA["lon"],
                        "ascend": [],
                    }
                ],
                schema_overrides={
                    "taxid": pl.Int32,
                    "zoom": pl.Int32,
                    "ascend": pl.List(pl.Int32),
                },
            ),
        ],
        how="diagonal_relaxed",
    )
    lm = lm.with_columns(
        pl.col("taxid").cast(pl.Int32),
        pl.col("lat").cast(pl.Float64),
        pl.col("lon").cast(pl.Float64),
        pl.col("zoom").fill_null(1).cast(pl.Int8),
        pl.col("sci_name").cast(pl.Utf8),
        pl.col("ascend").cast(pl.List(pl.Int32)),
        # depth=pl.col("ascend").list.len(),
        parent=pl.col("ascend").list.get(0, null_on_oob=True).cast(pl.Int32),
    )
    # Compute n_children
    parents = lm.get_column("parent").unique()
    lm = lm.with_columns(leaf=pl.col("taxid").is_in(parents).not_())
    # lm = lm.with_columns(
    #    child=pl.when(pl.col("leaf")).then(1).otherwise(None)
    # )
    # max_depth = lm.select(pl.col("depth").max()).item()
    # for depth in range(max_depth, 0, -1):
    #    lm = aggregate_depth(lm, "child", depth)
    # lm = lm.rename({"child": "n_children"})
    lm = lm.rename(
        {
            "lon": "pylifemap_x",
            "lat": "pylifemap_y",
            "zoom": "pylifemap_zoom",
            "ascend": "pylifemap_ascend",
            "leaf": "pylifemap_leaf",
            "parent": "pylifemap_parent",
        }
    )
    lm = lm.select(
        [
            "taxid",
            "pylifemap_zoom",
            "pylifemap_x",
            "pylifemap_y",
            "pylifemap_ascend",
            "pylifemap_leaf",
            "pylifemap_parent",
        ]
    )
    return lm


def export_lmdata() -> None:
    # Copy parquet file to lmdata directory
    try:
        features_file = BUILD_DIRECTORY / "TreeFeaturesComplete.parquet"
        features = pl.read_parquet(features_file)
        lmdata = convert_features(features)
        dest_file = LMDATA_DIRECTORY / "lmdata.parquet"
        lmdata.write_parquet(dest_file)
    except Exception as e:
        raise RuntimeError(f"Error exporting data to {dest_file}: {e}")

    logger.info(" Converting parquet file to Rdata file...")
    # Execute the R conversion script
    script_dir = Path(__file__).parent.absolute()
    script_file = script_dir / "Convert2Rdata.R"
    try:
        subprocess.run(["Rscript", str(script_file), BUILD_DIRECTORY])
    except Exception as e:
        raise RuntimeError(f"Error executing R script: {e}")

    logger.info(" Creating timestamp file...")
    # Get the current datetime
    now = datetime.now()
    # Format the datetime as a string in the desired format
    now_str = now.strftime("%Y%m%d%H%M")

    with open(LMDATA_DIRECTORY / "timestamp.txt", "w") as f:
        f.write(now_str)

    logger.info(" Copying parquet file to lmdata directory...")


if __name__ == "__main__":
    export_lmdata()
