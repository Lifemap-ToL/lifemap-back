import logging

import psycopg
from config import PSYCOPG_CONNECT_URL

logger = logging.getLogger("LifemapBuilder")


def db_connection() -> psycopg.Connection:
    """
    Connect to postgis database

    Returns
    -------
    psycopg.Connection
        Connection object.

    Raises
    ------
    RuntimeError
        If connection fails.
    """
    try:
        conn = psycopg.connect(
            PSYCOPG_CONNECT_URL
        )  # password will be directly retrieved from ~/.pgpassconn
    except Exception as e:
        raise RuntimeError(f"Unable to connect to the database: {e}")
    return conn


def init_db() -> None:
    """
    Create or recreate postgis database.
    """

    conn = db_connection()
    cur = conn.cursor()

    logger.info("Removing old tables...")
    cur.execute("DROP TABLE IF EXISTS points;")
    cur.execute("DROP TABLE IF EXISTS lines;")
    cur.execute("DROP TABLE IF EXISTS polygons;")
    conn.commit()

    logger.info("Creating new tables...")
    cur.execute(
        "CREATE TABLE points(id bigint,ref smallint,z_order smallint,branch boolean,tip boolean,zoomview integer,clade boolean,cladecenter boolean,rankame boolean,sci_name text,common_name_en text, common_name_fr text,full_name text,rank_en text, rank_fr text, name text, nbdesc integer,taxid text,geom_txt text, way geometry(POINT,3857));"
    )
    cur.execute(
        "CREATE TABLE lines(id bigint,ref smallint,z_order smallint,branch boolean,tip boolean,zoomview integer,clade boolean,cladecenter boolean,rankname boolean,sci_name text,common_name_en text, common_name_fr text, full_name text,rank_en text, rank_fr text, name text, nbdesc integer,taxid text,geom_txt text, way geometry(LINESTRING,3857));"
    )
    cur.execute(
        "CREATE TABLE polygons(id bigint,ref smallint,z_order smallint,branch boolean,tip boolean,zoomview integer,clade boolean,cladecenter boolean,rankame boolean,sci_name text,common_name_en text, common_name_fr text, full_name text,rank_en text, rank_fr text, name text, nbdesc integer,taxid text,geom_txt text, way geometry(POLYGON,3857));"
    )
    conn.commit()

    logger.info("Creating root node...")
    ##we include the root node
    cur.execute(
        "INSERT INTO points (id, sci_name, common_name_en, common_name_fr,rank_en, rank_fr,nbdesc,tip, zoomview,taxid,way) VALUES(1000000000, 'Root','Root','Root','Root','Root',1000000, FALSE, 1,1,ST_Transform(ST_GeomFromText('POINT(0 -4.226497)', 4326), 3857));"
    )
    conn.commit()

    conn.close()


def copy_db_to_prod() -> None:
    """
    Create production database tables from building ones.
    """
    conn = db_connection()
    cur = conn.cursor()

    for table in ["points", "lines", "polygons"]:
        logger.info(f"Copying {table}$...")
        cur.execute(f"DROP TABLE IF EXISTS {table}_prod;")
        cur.execute(f"CREATE TABLE {table}_prod AS TABLE {table};")

    conn.commit()
    conn.close()


def create_geometries() -> None:
    """
    Create geometry columns in postgis db tables from geom_txt columns.
    """

    conn = db_connection()
    cur = conn.cursor()

    for table in ["points", "lines", "polygons"]:
        logger.info(f"Creating {table} geometry")
        query = f"UPDATE {table} SET way = ST_Transform(ST_GeomFromText(geom_txt, 4326), 3857) WHERE way IS NULL;"
        cur.execute(query)
        conn.commit()

    logger.info("Dropping geom_txt columns")
    for table in ["points", "lines", "polygons"]:
        query = f"ALTER TABLE {table} DROP COLUMN geom_txt;"
        cur.execute(query)
        conn.commit()

    conn.close()


def create_index() -> None:
    """
    Apply create indes, clustering and analyzing on postgis geometries.
    """
    conn = db_connection()

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

    conn.close()
