"""Prepare one Solr additional-information file from formatted Parquet data."""

import logging
from pathlib import Path

import polars as pl
from config import BUILD_DIRECTORY


logger = logging.getLogger("LifemapBuilder")


def prepare_additional_info(source: str, info_file: Path) -> None:
    """Write one Parquet info file as JSON input for the Solr addi collection."""
    output_directory = BUILD_DIRECTORY / source
    output_directory.mkdir(parents=True, exist_ok=True)
    output_file = output_directory / "ADDITIONAL.json"
    logger.info("Reading additional information from %s", info_file)
    info = pl.read_parquet(info_file)
    tree_features = pl.read_json(output_directory / "TreeFeatures.json")
    tree_taxon_ids = tree_features.get_column("taxid").unique()
    info = info.filter(pl.col("taxon_id").is_in(tree_taxon_ids))
    info = info.rename({"taxon_id": "taxid"})
    logger.info("Writing additional information to %s", output_file)
    info.write_json(output_file)
