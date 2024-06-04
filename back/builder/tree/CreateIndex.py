import logging
import psycopg

from config import PSYCOPG_CONNECT_URL

logger = logging.getLogger("LifemapBuilder")


def create_index():

    ##CONNECT TO POSTGRESQL/POSTGIS DATABASE
    try:
        conn = psycopg.connect(
            PSYCOPG_CONNECT_URL
        )  # password will be directly retrieved from ~/.pgpassconn
    except Exception as e:
        raise RuntimeError(f"Unable to connect to the database: {e}")

    logger.info("Creating index...")
    cur = conn.cursor()
    cur.execute("CREATE INDEX IF NOT EXISTS linesid ON lines USING GIST(way);")
    cur.execute("CREATE INDEX IF NOT EXISTS pointsid ON points USING GIST(way);")
    cur.execute("CREATE INDEX IF NOT EXISTS polygid ON polygons USING GIST(way);")
    conn.commit()

    logger.info("Clustering...")
    cur.execute("CLUSTER lines USING linesid;")
    cur.execute("CLUSTER points USING pointsid;")
    cur.execute("CLUSTER polygons USING polygid;")
    conn.commit()

    logger.info("Analyzing...")
    cur.execute("ANALYZE lines;")
    cur.execute("ANALYZE points;")
    cur.execute("ANALYZE polygons;")
    conn.commit()

    logger.info("DONE...")
