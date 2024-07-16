"""
The goal of this script is to list which NCBI taxonomy ids are not present in wikidata.
Must be run after the builder has been run as it gets ncbi taxids from TreeFeaturesComplete.parquet.
"""

from pathlib import Path

import logging
import requests
import polars as pl

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

BUILD_DIRECTORY = Path.home() / ("builder_results")


def query_wikidata():
    url = "https://query.wikidata.org/sparql"

    taxids_query = """
    SELECT DISTINCT ?ncbiId WHERE {
        ?taxon wdt:P685 ?ncbiId.
    }
    """

    params = {"query": taxids_query, "format": "json"}

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed: HTTP {response.status_code}")


if __name__ == "__main__":
    logger.info("Querying wikidata for taxids")
    try:
        results = query_wikidata()
        wikidata_taxids = [
            result["ncbiId"]["value"] for result in results["results"]["bindings"]
        ]
        logger.info(f"Got {len(wikidata_taxids)} wikidata taxids")
    except Exception as e:
        print(f"Error: {e}")

    logger.info("Reading ncbi taxids from TreeFeaturesComplete.parquet")
    ncbi_taxids = pl.read_parquet(
        BUILD_DIRECTORY / "TreeFeaturesComplete.parquet"
    ).select("taxid", "sci_name")
    logger.info(f"Got {ncbi_taxids.height} ncbi taxids")

    logger.info("Computing missing taxids")
    missing_taxids = ncbi_taxids.filter(pl.col("taxid").is_in(wikidata_taxids).not_())
    logger.info(f"Got {missing_taxids.height} missing taxids")

    logger.info("Saving missing taxids to missing_wikidata_taxids.parquet")
    missing_taxids.write_parquet(BUILD_DIRECTORY / "missing_wikidata_taxids.parquet")
    logger.info("Done")
