#!/usr/bin/python3

import polars as pl

import logging

from config import BUILD_DIRECTORY

logger = logging.getLogger("LifemapBuilder")


def MergeJsons(f1, f2, output):

    d1 = pl.read_json(BUILD_DIRECTORY / f1).select(
        ["taxid", "sci_name", "zoom", "lat", "lon"]
    )
    d2 = pl.read_json(BUILD_DIRECTORY / f2).select(["taxid", "ascend"])
    d = d1.join(d2, on="taxid", how="left")

    d.write_json(BUILD_DIRECTORY / output, row_oriented=True)


def merge_all():
    for i in range(1, 4):
        logger.info(f"Merging tree {i}")
        MergeJsons(
            f"TreeFeatures{i}.json",
            f"ADDITIONAL.{i}.json",
            f"TreeFeaturesComplete{i}.json",
        )
