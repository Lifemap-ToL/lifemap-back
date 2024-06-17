#!/usr/bin/python

import json
import logging

import polars as pl
from config import BUILD_DIRECTORY, GENOMES_DIRECTORY, TAXO_DIRECTORY
from ete3 import Tree
from utils import download_file_if_newer
from tqdm import tqdm

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
        pl.col("node").cast(pl.Utf8).alias("taxid")
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

    # Get age
    # taxid_age = ages.filter(pl.col("node") == n.taxid)
    # if taxid_age.height == 1:
    #     n.age = taxid_age.get_column("age").item()
    # else:
    #     n.age = 0
    # Get nbgenomes
    # taxid_genomes = genomes.filter(pl.col("taxid") == n.taxid)
    # if taxid_genomes.height == 1:
    #     nb_genomes = taxid_genomes.get_column("n").item()
    # else:
    #     nb_genomes = 0
    # try:
    #     n.nbgenomes += nb_genomes
    # except AttributeError:
    #     n.nbgenomes = nb_genomes
    # node = n
    # while node.up:
    #     try:
    #         node.up.nbgenomes += nb_genomes
    #     except AttributeError:
    #         node.up.nbgenomes = nb_genomes
    #     n.path.append(node.up.taxid)
    #     node = node.up

    ##traverse to write
    # logger.info("  Second traverse")
    # addi = []
    # for n in tqdm(t.traverse(), total=len(t)):
    #     n_data = {
    #         "taxid": n.taxid,
    #         "genomes": n.nbgenomes,
    #         "ascend": n.path + [0],
    #         # "age": n.age,
    #     }
    #     addi.append(n_data)

    logger.info("  Saving to json")
    addi.write_json(BUILD_DIRECTORY / f"ADDITIONAL.{nbgroup}.json", row_oriented=True)
