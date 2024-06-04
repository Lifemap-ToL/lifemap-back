from pathlib import Path
from dotenv import dotenv_values

BUILD_DIRECTORY = Path.home() / ("build_results")
TAXO_DIRECTORY = BUILD_DIRECTORY / "taxo"
GENOMES_DIRECTORY = BUILD_DIRECTORY / "genomes"

# LMDATA_DIRECTORY = "/var/www/html/data"
LMDATA_DIRECTORY = BUILD_DIRECTORY / "lmdata"

config = dotenv_values(".env")

DB_HOST = "localhost"
DB_NAME = config["PG_DB"]
DB_USER = config["PG_USER"]
DB_PASSWD = config["PG_PASSWD"]

PSYCOPG_CONNECT_URL = (
    f"dbname='{DB_NAME}' user='{DB_USER}' host='{DB_HOST}' password='{DB_PASSWD}'"
)
