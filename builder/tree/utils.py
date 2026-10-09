"""
Utility functions
"""

import logging
import os
from collections import defaultdict
from datetime import datetime
from ftplib import FTP
from pathlib import Path

import polars as pl
import requests
from config import TAXO_DIRECTORY

logger = logging.getLogger("LifemapBuilder")

LUCA = {"lat": -4.226497, "lon": 0}


def download_ftp_file_if_newer(host, remote_file, local_file) -> bool:
    downloaded = False
    try:
        with FTP(host) as ftp:
            ftp.login()

            # Get the modification time of the remote file
            remote_mtime = ftp.sendcmd(f"MDTM {remote_file}")
            remote_mtime = datetime.strptime(remote_mtime[4:], "%Y%m%d%H%M%S")

            try:
                # Get the modification time of the local file
                local_mtime = datetime.fromtimestamp(os.path.getmtime(local_file))
            except FileNotFoundError:
                # If the local file doesn't exist, download the remote file
                local_mtime = datetime(1970, 1, 1)

            # Download the remote file if it's newer than the local file
            if remote_mtime > local_mtime:
                with open(local_file, "wb") as f:
                    ftp.retrbinary(f"RETR {remote_file}", f.write)
                logger.info(f"Downloaded {remote_file} (newer than local file)")
                downloaded = True
            else:
                logger.info(f"Remote file {remote_file} is not newer than local file, skipping download")

    except Exception as e:
        logger.error(f"Error downloading file: {e}")

    return downloaded


def download_github_file_if_newer(github_url: str, local_file: Path | str) -> bool:
    downloaded = False
    try:
        # Get the last modified time of the github file
        api_url = github_url.replace("github.com", "api.github.com/repos")
        api_url = api_url.replace("/blob/main/", "/contents/")
        api_url = api_url.replace("/blob/master/", "/contents/")
        response = requests.get(api_url, timeout=30)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch {github_url} metadata.")
            return False

        remote_last_modified = datetime.strptime(
            response.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S %Z"
        )

        # Get the last modified time of the local file
        local_path = Path(local_file)
        if local_path.exists():
            local_last_modified = datetime.fromtimestamp(local_path.stat().st_mtime)
        else:
            local_last_modified = datetime.min  # Treat as very old if the file doesn't exist

        # Compare and download if remote is newer
        if remote_last_modified > local_last_modified:
            download_url = response.json()["download_url"]
            r = requests.get(download_url, timeout=30)
            local_path.write_bytes(r.content)
            downloaded = True
            logger.info(f"Downloaded {github_url} (newer than local file)")
        else:
            logger.info(f"Remote file {github_url} is not newer than local file, skipping download")

    except Exception as e:
        logger.error(f"Error downloading file: {e}")

    return downloaded


def get_vernacular_names(lang: str) -> dict[str, list[str]]:
    """Read vernacular names for one language from taxonomy-all."""
    logger.info(f"  Importing {lang} common names")

    filename = f"TAXONOMIC-VERNACULAR-{lang.upper()}-LATEST.txt"
    github_url = f"https://github.com/Lifemap-ToL/taxonomy-all/blob/main/{lang}/{filename}"
    local_file = TAXO_DIRECTORY / filename

    download_github_file_if_newer(github_url, local_file)

    names = defaultdict(list)
    with open(local_file, encoding="utf-8") as file:
        for line in file:
            columns = line.rstrip("\n").split("\t")
            taxid = columns[0].strip()
            name = columns[2].strip()

            if name and name not in names[taxid]:
                names[taxid].append(name)

    return names


def get_ranks_translations() -> dict:
    """
    Import rank translations for all configured languages from ranks.csv

    Returns
    -------
    dict
        dictionary of translations.
    """
    logger.info("  Importing translated rank names")
    trans_df = pl.read_csv(TAXO_DIRECTORY / "ranks.csv")
    trans = {}
    langs = trans_df.columns
    langs.remove("en")
    for row in trans_df.iter_rows(named=True):
        rank = row["en"].strip()
        trans[rank] = {lang: row[lang].strip() for lang in langs}
    return trans
