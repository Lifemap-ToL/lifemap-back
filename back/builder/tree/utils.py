"""
Utility functions
"""

import os
from datetime import datetime
from ftplib import FTP


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
