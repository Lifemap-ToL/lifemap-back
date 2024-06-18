import logging
import polars as pl
from config import TAXO_DIRECTORY
from db import db_connection

logger = logging.getLogger("LifemapBuilder")


def check_ranks() -> None:
    """
    Compare english rank values in ranks.csv and in the NCBI data
    stored in postgis.
    """
    trans_df = pl.read_csv(TAXO_DIRECTORY / "ranks.csv")
    ranks_csv = trans_df.select(pl.col("en").unique()).get_column("en").to_list()
    ranks_csv = set(ranks_csv)
    conn = db_connection()
    cur = conn.cursor()
    query = "select distinct rank_en  from points_prod where rank_en is not null;"
    cur.execute(query)
    ranks_db = cur.fetchall()
    ranks_db = {rank[0] for rank in ranks_db}
    conn.close()

    not_in_db = ranks_db - ranks_csv
    if not_in_db != {"Root"}:
        msg = f"Ranks in database but not in ranks.csv: {not_in_db}"
        logger.warning(msg)

    not_in_csv = ranks_csv - ranks_db
    if not_in_db:
        msg = f"Ranks in ranks.csv but not in database: {not_in_csv}"
        logger.warning(msg)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # logger = logging.getLogger()
    check_ranks()
