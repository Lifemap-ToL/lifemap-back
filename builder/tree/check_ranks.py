import logging

import polars as pl
from config import TAXO_DIRECTORY
from db import db_connection

logger = logging.getLogger("LifemapBuilder")


def check_ranks() -> None:
    """
    Warn about taxonomy ranks without a translation in ranks.csv.
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

    missing_ranks = ranks_db - ranks_csv
    missing_ranks.discard("Root")
    if missing_ranks:
        msg = f"Ranks in database but not in ranks.csv: {missing_ranks}"
        logger.warning(msg)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # logger = logging.getLogger()
    check_ranks()
