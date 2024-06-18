import logging

import psycopg
from config import PSYCOPG_CONNECT_URL

logger = logging.getLogger("LifemapBuilder")

TABLES = ["points", "branches", "polygons", "ranks", "cladecenters"]


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
    for table in TABLES:
        cur.execute(f"DROP TABLE IF EXISTS {table};")  # type: ignore
    conn.commit()

    logger.info("Creating new tables...")
    cur.execute(
        "CREATE TABLE points (id bigint,ref smallint,z_order smallint,branch boolean,tip boolean,zoomview integer,clade boolean,cladecenter boolean,rankname boolean,sci_name text,common_name_en text, full_name text,rank_en text, name text, nbdesc integer,taxid text,geom_txt text, way geometry(POINT,3857));"
    )
    cur.execute(
        "CREATE TABLE branches (id bigint,ref smallint,z_order smallint,branch boolean,tip boolean,zoomview integer,clade boolean,cladecenter boolean,rankname boolean,sci_name text,common_name_en text,  full_name text,rank_en text, name text, nbdesc integer,taxid text,geom_txt text, way geometry(LINESTRING,3857));"
    )
    cur.execute(
        "CREATE TABLE polygons (id bigint,ref smallint,z_order smallint,branch boolean,tip boolean,zoomview integer,clade boolean,cladecenter boolean,rankname boolean,sci_name text,common_name_en text,  full_name text,rank_en text, name text, nbdesc integer,taxid text,geom_txt text, way geometry(POLYGON,3857));"
    )
    cur.execute(
        "CREATE TABLE ranks (id bigint,ref smallint,z_order smallint,branch boolean,tip boolean,zoomview integer,clade boolean,cladecenter boolean,rankname boolean,sci_name text,common_name_en text,  full_name text,rank_en text, name text, nbdesc integer,taxid text,geom_txt text, way geometry(LINESTRING,3857));"
    )
    cur.execute(
        "CREATE TABLE cladecenters (id bigint,ref smallint,z_order smallint,branch boolean,tip boolean,zoomview integer,clade boolean,cladecenter boolean,rankname boolean,sci_name text,common_name_en text, full_name text,rank_en text, name text, nbdesc integer,taxid text,geom_txt text, way geometry(POINT,3857));"
    )
    conn.commit()

    logger.info("Creating root node...")
    ##we include the root node
    cur.execute(
        "INSERT INTO points (id, sci_name, common_name_en, rank_en, nbdesc,tip, zoomview,taxid,way) VALUES(1000000000, 'Root','Root','Root',1000000, FALSE, 1,1,ST_Transform(ST_GeomFromText('POINT(0 -4.226497)', 4326), 3857));"
    )
    conn.commit()

    conn.close()


def copy_db_to_prod() -> None:
    """
    Create production database tables from building ones.
    """
    conn = db_connection()
    cur = conn.cursor()

    for table in TABLES:
        logger.info(f"Copying {table}...")
        cur.execute(f"DROP TABLE IF EXISTS {table}_prod;")  # type: ignore
        cur.execute(f"CREATE TABLE {table}_prod AS TABLE {table};")  # type: ignore

    conn.commit()
    conn.close()


def create_geometries() -> None:
    """
    Create geometry columns in postgis db tables from geom_txt columns.
    """

    conn = db_connection()
    cur = conn.cursor()

    for table in TABLES:
        logger.info(f"Creating {table} geometry")
        query = f"UPDATE {table} SET way = ST_Transform(ST_GeomFromText(geom_txt, 4326), 3857) WHERE way IS NULL;"
        cur.execute(query)  # type: ignore
        conn.commit()

    logger.info("Dropping geom_txt columns")
    for table in TABLES:
        query = f"ALTER TABLE {table} DROP COLUMN geom_txt;"
        cur.execute(query)  # type: ignore
        conn.commit()

    conn.close()


def create_index() -> None:
    """
    Apply create index, clustering and analyzing on postgis geometries.
    """
    conn = db_connection()
    cur = conn.cursor()

    logger.info("Creating index...")
    cur.execute(
        "CREATE INDEX IF NOT EXISTS branches_prod_id ON branches_prod USING GIST(way);"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS ranks_prod_id ON ranks_prod USING GIST(way);"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS points_prod_id ON points_prod USING GIST(way);"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS cladecenters_prod_id ON cladecenters_prod USING GIST(way);"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS polygons_prod_id ON polygons_prod USING GIST(way);"
    )
    conn.commit()

    logger.info("Clustering...")
    cur.execute("CLUSTER branches_prod USING branches_prod_id;")
    cur.execute("CLUSTER ranks_prod USING ranks_prod_id;")
    cur.execute("CLUSTER points_prod USING points_prod_id;")
    cur.execute("CLUSTER cladecenters_prod USING cladecenters_prod_id;")
    cur.execute("CLUSTER polygons_prod USING polygons_prod_id;")
    conn.commit()

    logger.info("Analyzing...")
    cur.execute("ANALYZE branches_prod;")
    cur.execute("ANALYZE ranks_prod;")
    cur.execute("ANALYZE points_prod;")
    cur.execute("ANALYZE cladecenters_prod;")
    cur.execute("ANALYZE polygons_prod;")
    conn.commit()

    conn.close()
