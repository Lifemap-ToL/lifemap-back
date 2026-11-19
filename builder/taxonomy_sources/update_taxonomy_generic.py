"""Update source data and prepare formatted Parquet files."""

import argparse
from pathlib import Path

import prepare_ncbi


DATASET_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "taxonomy_datasets"


def update_source(source: str) -> None:
    source_directory = DATASET_DIRECTORY / source

    if source == "ncbi":
        prepare_ncbi.prepare_taxonomy(source_directory)
    else:
        print(f"No automatic download for {source}.")
        print(f"Using existing data in {source_directory / 'formatted_data'}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    args = parser.parse_args()

    update_source(args.source)
