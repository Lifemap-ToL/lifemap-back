from pathlib import Path

from dotenv import dotenv_values

config = dotenv_values(".env")

DB_HOST = "localhost"
DB_NAME = config["PG_DB"]
DB_USER = config["PG_USER"]
DB_PASSWD = config["PG_PASSWD"]

if config["BUILD_RESULTS_DIR"] is None:
    msg = "Missing BUILD_RESULTS_DIR in .env"
    raise ValueError(msg)

BUILD_DIRECTORY = Path(config["BUILD_RESULTS_DIR"])
BUILD_DIRECTORY.mkdir(exist_ok=True)

TAXO_DIRECTORY = BUILD_DIRECTORY / "taxo"
TAXO_DIRECTORY.mkdir(exist_ok=True)
GENOMES_DIRECTORY = BUILD_DIRECTORY / "genomes"
GENOMES_DIRECTORY.mkdir(exist_ok=True)
LMDATA_DIRECTORY = BUILD_DIRECTORY / "lmdata"
LMDATA_DIRECTORY.mkdir(exist_ok=True)

LANG_LIST = ["en", "es", "fr", "de", "el"]

PSYCOPG_CONNECT_URL = f"dbname='{DB_NAME}' user='{DB_USER}' host='{DB_HOST}' password='{DB_PASSWD}'"
