"""
Utility functions
"""

import logging
import os
import pickle
from collections import defaultdict
from datetime import datetime
from ftplib import FTP
from pathlib import Path

import polars as pl
import requests
from config import TAXO_DIRECTORY

logger = logging.getLogger("LifemapBuilder")


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
                print(f"Downloaded {remote_file} (newer than local file)")
                downloaded = True
            else:
                print(f"Remote file {remote_file} is not newer than local file, skipping download")

    except Exception as e:
        print(f"Error downloading file: {e}")

    return downloaded


def download_github_file_if_newer(github_url: str, local_file: Path | str) -> bool:
    downloaded = False
    try:
        # Get the last modified time of the github file
        api_url = github_url.replace("github.com", "api.github.com/repos").replace(
            "/blob/master/", "/contents/"
        )
        response = requests.get(api_url)
        if response.status_code != 200:
            print(f"Failed to fetch {github_url} metadata.")
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
            r = requests.get(download_url)
            local_path.write_bytes(r.content)
            downloaded = True
            print(f"Downloaded {github_url} (newer than local file)")
        else:
            print(f"Remote file {github_url} is not newer than local file, skipping download")

    except Exception as e:
        print(f"Error downloading file: {e}")

    return downloaded


def get_translations_fr() -> dict[str, set]:
    """
    Import french translations of taxonomy as dictionary from:
    https://github.com/Lifemap-ToL/taxonomy-fr/blob/master/TAXONOMIC-VERNACULAR-FR-LATEST.txt

    There can be several common names for one sciname, so each dict value is a list.

    Returns
    -------
    dict
        dictionary of translations.
    """
    logger.info("  Importing french common names")
    github_url = "https://github.com/Lifemap-ToL/taxonomy-fr/blob/master/TAXONOMIC-VERNACULAR-FR-LATEST.txt"
    local_file = TAXO_DIRECTORY / "TAXONOMIC-VERNACULAR-FR-LATEST.txt"
    pkl_file = TAXO_DIRECTORY / "fr_common_name.pkl"

    downloaded = download_github_file_if_newer(github_url=github_url, local_file=local_file)

    if not downloaded and pkl_file.exists():
        logger.info(f"  Importing from {pkl_file}")
        with open(pkl_file, "rb") as f:
            trans = pickle.load(f)
    else:
        trans = defaultdict(set)
        with open(local_file) as f:
            lines = f.readlines()
        lines = [line.split("\t") for line in lines]
        for taxid, _, vernacular_name in lines:
            trans[taxid.strip()].add(vernacular_name.strip())
        with open(pkl_file, "wb") as f:
            pickle.dump(trans, f)
    return trans


def get_ranks_translations() -> dict:
    """
    Import french translations of ranks as dictionary from ranks.csv

    Returns
    -------
    dict
        dictionary of translations.
    """
    logger.info("  Importing french rank names")
    trans_df = pl.read_csv(TAXO_DIRECTORY / "ranks.csv")
    trans = {}
    langs = trans_df.columns
    langs.remove("en")
    for row in trans_df.iter_rows(named=True):
        rank = row["en"].strip()
        trans[rank] = {lang: row[lang].strip() for lang in langs}
    return trans
