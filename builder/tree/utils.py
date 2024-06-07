"""
Utility functions
"""

import logging
import os
import pickle
from collections import defaultdict
from datetime import datetime
from ftplib import FTP

from config import TAXO_DIRECTORY

logger = logging.getLogger("LifemapBuilder")


def download_file_if_newer(host, remote_file, local_file) -> bool:
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
                print(
                    f"Remote file {remote_file} is not newer than local file, skipping download"
                )

    except Exception as e:
        print(f"Error downloading file: {e}")

    return downloaded


def get_translations_fr() -> dict:
    """
    Import french translations of taxonomy as dictionary from TAXONOMIC-VERNACULAR-FR.txt

    There can be several common names for one sciname, so each dict value is a list.

    Returns
    -------
    dict
        dictionary of translations.
    """
    logger.info("  Importing french common names")
    pkl_file = TAXO_DIRECTORY / "fr_common_name.pkl"
    if pkl_file.exists():
        logger.info(f"  Importing from {pkl_file}")
        with open(pkl_file, "rb") as f:
            trans = pickle.load(f)
    else:
        trans = defaultdict(list)
        with open(TAXO_DIRECTORY / "TAXONOMIC-VERNACULAR-FR.txt") as f:
            lines = f.readlines()
        lines = [line.split("\t") for line in lines]
        for k, v in lines:
            trans[k.strip()].append(v.strip())
        with open(pkl_file, "wb") as f:
            pickle.dump(trans, f)
    return trans


def get_ranks_fr() -> dict:
    """
    Import french translations of ranks as dictionary from ranks.txt

    Returns
    -------
    dict
        dictionary of translations.
    """
    logger.info("  Importing french rank names")
    with open(TAXO_DIRECTORY / "ranks.txt") as f:
        lines = f.readlines()
    lines = [line.split("\t") for line in lines]
    trans = {k.strip(): v.strip() for k, v in lines}
    return trans
