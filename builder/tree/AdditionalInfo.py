#!/usr/bin/python

import logging

import polars as pl
from config import BUILD_DIRECTORY, GENOMES_DIRECTORY, TAXO_DIRECTORY
from utils import download_file_if_newer

logger = logging.getLogger("LifemapBuilder")


def download_genomes() -> None:
    for name in ["eukaryotes", "prokaryotes"]:
        genome_downloaded = download_file_if_newer(
            host="ftp.ncbi.nlm.nih.gov",
            remote_file=f"genomes/GENOME_REPORTS/{name}.txt",
            local_file=GENOMES_DIRECTORY / f"{name}.txt",
        )
        if genome_downloaded or not (GENOMES_DIRECTORY / f"{name}.parquet").exists():
            d = pl.read_csv(
                GENOMES_DIRECTORY / f"{name}.txt",
                separator="\t",
                infer_schema_length=20000,
                null_values=["-"],
            )
            # For the moment we only keep the total number of complete genomes
            # by taxid
            d = (
                d.filter(pl.col("Status") == "Complete Genome")
                .group_by("TaxID")
                .len(name="n")
                .select(pl.col("TaxID").cast(pl.Utf8).alias("taxid"), pl.col("n"))
            )
            d.write_parquet(GENOMES_DIRECTORY / f"{name}.parquet")
    eu = pl.read_parquet(GENOMES_DIRECTORY / "eukaryotes.parquet")
    pro = pl.read_parquet(GENOMES_DIRECTORY / "prokaryotes.parquet")
    genomes = eu.vstack(pro)
    genomes.write_parquet(GENOMES_DIRECTORY / "genomes.parquet")
    logger.info("Genomes info downloaded and saved to parquet.")


def add_info(nbgroup: str):

    #######################################################################################################################
    ##                       NOW WE RETRIEVE WHAT WE WILL PUT IN THE JSON FILES
    #######################################################################################################################

    logger.info("  Loading data...")
    ascends = pl.read_parquet(BUILD_DIRECTORY / f"ascends_{nbgroup}.parquet")

    genomes = pl.read_parquet(GENOMES_DIRECTORY / "genomes.parquet")
    ages = pl.read_csv(TAXO_DIRECTORY / "timetreetimes.csv").with_columns(
        pl.col("node").cast(pl.Utf8).alias("taxid"), pl.col("age").round(1)
    )

    addi = ascends
    ascend = ascends.with_columns(
        pl.col("ascend").list.concat(pl.col("taxid"))
    ).explode("ascend")
    logger.info("  Merging additional data...")
    n_genomes = (
        ascend.join(genomes, left_on="taxid", right_on="taxid", how="left")
        .with_columns(pl.col("n").fill_null(0))
        .group_by("ascend")
        .agg(genomes=pl.sum("n"))
        .rename({"ascend": "taxid"})
    )
    addi = addi.join(n_genomes, on="taxid", how="left").with_columns(
        pl.col("genomes").fill_null(0)
    )

    addi = addi.join(ages, on="taxid", how="left")

    logger.info("  Saving to json...")
    addi.write_json(BUILD_DIRECTORY / f"ADDITIONAL.{nbgroup}.json", row_oriented=True)


def merge_features() -> None:

    logger.info("  Merging tree and additional features...")
    features = []
    for i in range(1, 4):
        ascends = pl.read_parquet(BUILD_DIRECTORY / f"ascends_{i}.parquet")
        tree_features = pl.read_json(BUILD_DIRECTORY / f"TreeFeatures{i}.json").select(
            ["taxid", "sci_name", "zoom", "lat", "lon"]
        )
        merged = tree_features.join(ascends, on="taxid", how="left")
        features.append(merged)

    logger.info("  Combining and saving merged features...")
    features = pl.concat(features)
    features.write_parquet(BUILD_DIRECTORY / "TreeFeaturesComplete.parquet")
