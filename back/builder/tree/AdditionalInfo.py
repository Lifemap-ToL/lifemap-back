#!/usr/bin/python

import json
import logging

import polars as pl
from config import BUILD_DIRECTORY, GENOMES_DIRECTORY
from ete3 import Tree
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


def add_info(groupnb: str):

    #######################################################################################################################
    ##                       NOW WE RETRIEVE WHAT WE WILL PUT IN THE JSON FILES
    #######################################################################################################################

    if groupnb == "1":
        t = Tree(str(BUILD_DIRECTORY / "ARCHAEA"))
    if groupnb == "2":
        t = Tree(str(BUILD_DIRECTORY / "EUKARYOTES"))
    if groupnb == "3":
        t = Tree(str(BUILD_DIRECTORY / "BACTERIA"))

    genomes = pl.read_parquet(GENOMES_DIRECTORY / "genomes.parquet")

    ##traverse first time:
    for n in t.traverse():
        n.path = []
        taxid_genomes = genomes.filter(pl.col("taxid") == n.taxid)
        if taxid_genomes.height == 1:
            nb_genomes = taxid_genomes.get_column("n").item()
        else:
            nb_genomes = 0
        try:
            n.nbgenomes += nb_genomes
        except AttributeError:
            n.nbgenomes = nb_genomes
        node = n
        while node.up:
            try:
                node.up.nbgenomes += nb_genomes
            except AttributeError:
                node.up.nbgenomes = nb_genomes
            n.path.append(node.up.taxid)
            node = node.up

    ##traverse to write
    addi = []
    for n in t.traverse():
        n_data = {"taxid": n.taxid, "genomes": n.nbgenomes, "ascend": n.path + [0]}
        addi.append(n_data)

    with open(BUILD_DIRECTORY / f"ADDITIONAL.{groupnb}.json", "w") as f:
        json.dump(addi, f)
