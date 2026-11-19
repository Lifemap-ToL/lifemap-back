"""Export data produced by the Parquet-based tree builder."""

import logging
from datetime import datetime
from pathlib import Path

import polars as pl
from config import BUILD_DIRECTORY
from utils import LUCA


logger = logging.getLogger("LifemapBuilder")


def source_directory(source: str) -> Path:
    directory = BUILD_DIRECTORY / source
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def convert_features(features: pl.DataFrame) -> pl.DataFrame:
    features = pl.concat(
        [
            features,
            pl.DataFrame(
                [
                    {
                        "taxid": "0",
                        "sci_name": "Luca",
                        "zoom": 5,
                        "lat": LUCA["lat"],
                        "lon": LUCA["lon"],
                        "ascend": [],
                    }
                ],
                schema_overrides={"taxid": pl.String, "ascend": pl.List(pl.String)},
            ),
        ],
        how="diagonal_relaxed",
    )
    features = features.with_columns(
        pl.col("taxid").cast(pl.String),
        pl.col("lat").cast(pl.Float64),
        pl.col("lon").cast(pl.Float64),
        pl.col("zoom").fill_null(1).cast(pl.Int8),
        pl.col("sci_name").cast(pl.String),
        pl.col("ascend").cast(pl.List(pl.String)),
        parent=pl.col("ascend").list.get(0, null_on_oob=True).cast(pl.String),
    )

    parents = features.get_column("parent").unique()
    features = features.with_columns(leaf=pl.col("taxid").is_in(parents).not_())
    features = features.rename(
        {
            "lon": "pylifemap_x",
            "lat": "pylifemap_y",
            "zoom": "pylifemap_zoom",
            "ascend": "pylifemap_ascend",
            "leaf": "pylifemap_leaf",
            "parent": "pylifemap_parent",
        }
    )
    return features.select(
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


def export_lmdata(source: str, info_file: Path) -> None:
    output_directory = source_directory(source)
    features = pl.read_json(output_directory / "TreeFeatures.json")
    info = pl.read_parquet(info_file).select(
        pl.col("taxon_id").alias("taxid"), "ascend"
    )
    features = features.join(info, on="taxid", how="left")
    features_file = output_directory / "TreeFeaturesComplete.parquet"
    features.write_parquet(features_file)

    features.write_parquet(output_directory / "lmdata_R.parquet", compression="lz4")
    convert_features(features).write_parquet(output_directory / "lmdata.parquet")

    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    (output_directory / "timestamp.txt").write_text(timestamp)
