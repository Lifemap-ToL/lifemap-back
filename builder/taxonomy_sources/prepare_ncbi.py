"""Download NCBI taxonomy data and prepare simple Parquet files."""

import argparse
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import polars as pl
import requests


NCBI_TAXDUMP_URL = "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz"
NCBI_GENOMES_URL = "https://ftp.ncbi.nlm.nih.gov/genomes/GENOME_REPORTS/{name}.txt"
TAXONOMY_ALL_URL = (
    "https://raw.githubusercontent.com/Lifemap-ToL/taxonomy-all/main/"
    "{language}/TAXONOMIC-VERNACULAR-{language_upper}-LATEST.txt"
)
LANGUAGES = ["en", "es", "fr", "de", "el"]
AGE_FILE = Path(__file__).parent.parent / "taxo" / "timetreetimes.csv"


def download_file(url: str, filename: Path) -> bool:
    if filename.exists():
        response = requests.head(url, timeout=30, allow_redirects=True)
        remote_date = response.headers.get("Last-Modified")

        if not remote_date:
            print(f"Using existing {filename.name}.")
            return False

        remote_time = datetime.strptime(remote_date, "%a, %d %b %Y %H:%M:%S %Z")
        remote_time = remote_time.replace(tzinfo=timezone.utc)
        local_time = datetime.fromtimestamp(filename.stat().st_mtime, tz=timezone.utc)

        if remote_time <= local_time:
            print(f"Using existing {filename.name}.")
            return False

        print(f"Downloading newer {filename.name}...")
    else:
        print(f"Downloading {filename.name}...")

    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()

    with filename.open("wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            file.write(chunk)

    return True


def read_ncbi_names(filename: Path) -> dict[str, dict[str, object]]:
    names = {}

    with filename.open(encoding="utf-8") as file:
        for line in file:
            columns = [column.strip() for column in line.split("|")]
            taxon_id, name, name_type = columns[0], columns[1], columns[3]

            taxon = names.setdefault(
                taxon_id,
                {
                    "scientific_name": "",
                    "authority": "",
                    "synonyms": [],
                },
            )

            if name_type == "scientific name":
                taxon["scientific_name"] = name
            elif name_type == "authority":
                taxon["authority"] = name
            elif name_type == "synonym":
                taxon["synonyms"].append(name)  # type: ignore[union-attr]

    return names


def create_taxonomy_file(nodes_file: Path, names_file: Path, output_file: Path) -> None:
    names = read_ncbi_names(names_file)
    rows = []

    with nodes_file.open(encoding="utf-8") as file:
        for line in file:
            columns = [column.strip() for column in line.split("|")]
            taxon_id, parent_taxon_id, rank = columns[0], columns[1], columns[2]
            taxon_names = names[taxon_id]

            if taxon_id == parent_taxon_id:
                parent_taxon_id = ""

            rows.append(
                {
                    "taxon_id": taxon_id,
                    "parent_taxon_id": parent_taxon_id,
                    "scientific_name": taxon_names["scientific_name"],
                    "rank": rank,
                    "authority": taxon_names["authority"],
                    "synonyms": taxon_names["synonyms"],
                }
            )

    pl.DataFrame(rows).write_parquet(output_file)


def read_vernacular_names(filename: Path, language: str) -> list[dict[str, object]]:
    rows = []

    with filename.open(encoding="utf-8") as file:
        for line in file:
            columns = line.rstrip("\n").split("\t")
            taxon_id, name = columns[0].strip(), columns[2].strip()

            if name:
                rows.append(
                    {
                        "taxon_id": taxon_id,
                        "language": language,
                        "name": name,
                    }
                )

    return rows


def create_names_file(output_file: Path, downloads_directory: Path) -> None:
    rows = []

    for language in LANGUAGES:
        url = TAXONOMY_ALL_URL.format(
            language=language,
            language_upper=language.upper(),
        )
        filename = downloads_directory / (
            f"TAXONOMIC-VERNACULAR-{language.upper()}-LATEST.txt"
        )
        download_file(url, filename)
        rows.extend(read_vernacular_names(filename, language))

    pl.DataFrame(rows).unique().write_parquet(output_file)


def create_info_file(taxonomy_file: Path) -> pl.DataFrame:
    taxonomy = pl.read_parquet(taxonomy_file)
    parents = dict(taxonomy.select("taxon_id", "parent_taxon_id").iter_rows())
    rows = []

    print(f"Computing ascend for {len(parents)} taxa...")
    for number, (taxon_id, parent_taxon_id) in enumerate(parents.items(), start=1):
        if number % 500_000 == 0:
            print(f"  processed {number} taxa")
        ascend = []
        parent = parent_taxon_id

        while parent and parent != taxon_id:
            ascend.append(parent)
            next_parent = parents[parent]
            if next_parent == parent:
                break
            parent = next_parent

        if not ascend or ascend[-1] != "0":
            ascend.append("0")
        rows.append({"taxon_id": taxon_id, "ascend": ascend})

    return pl.DataFrame(rows)


def download_genomes(downloads_directory: Path) -> list[Path]:
    files = []

    for name in ["eukaryotes", "prokaryotes"]:
        filename = downloads_directory / f"{name}.txt"
        download_file(NCBI_GENOMES_URL.format(name=name), filename)
        files.append(filename)

    return files


def read_genomes(files: list[Path]) -> pl.DataFrame:
    genomes = []

    for filename in files:
        print(f"Reading {filename.name}...")
        data = pl.read_csv(
            filename,
            separator="\t",
            infer_schema_length=20000,
            null_values=["-"],
            quote_char=None,
        )
        genomes.append(
            data.filter(pl.col("Status") == "Complete Genome")
            .select(pl.col("TaxID").cast(pl.String).alias("taxon_id"))
        )

    genomes = pl.concat(genomes).group_by("taxon_id").len(name="genomes")
    total_genomes = genomes["genomes"].sum()
    print(f"Found {total_genomes} complete genomes for {genomes.height} taxa.")
    return genomes


def add_genomes(
    info: pl.DataFrame,
    genomes: pl.DataFrame,
    taxonomy_file: Path,
) -> pl.DataFrame:
    taxonomy = pl.read_parquet(taxonomy_file, columns=["taxon_id", "parent_taxon_id"])
    parents = dict(taxonomy.iter_rows())
    genome_counts = {}

    total_genomes = genomes["genomes"].sum()
    print(
        f"Adding {total_genomes} complete genomes from "
        f"{genomes.height} taxa to their ancestors..."
    )
    for row in genomes.iter_rows(named=True):
        taxon_id = row["taxon_id"]
        count = row["genomes"]
        parent = taxon_id

        while parent in parents:
            genome_counts[parent] = genome_counts.get(parent, 0) + count
            next_parent = parents[parent]
            if next_parent == parent:
                break
            parent = next_parent

    genome_counts = pl.DataFrame(
        {
            "taxon_id": list(genome_counts),
            "genomes": list(genome_counts.values()),
        }
    )
    return (
        info.join(genome_counts, on="taxon_id", how="left")
        .with_columns(pl.col("genomes").fill_null(0))
    )


def add_age(info_file: Path) -> None:
    info = pl.read_parquet(info_file)
    ages = pl.read_csv(AGE_FILE).select(
        pl.col("node").cast(pl.String).alias("taxon_id"),
        pl.col("age").round(1),
    )
    info.join(ages, on="taxon_id", how="left").write_parquet(info_file)


def prepare_taxonomy(source_directory: Path) -> None:
    downloads_directory = source_directory / "downloads"
    output_directory = source_directory / "formatted_data"
    source_directory.mkdir(parents=True, exist_ok=True)
    downloads_directory.mkdir(parents=True, exist_ok=True)
    output_directory.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory() as directory:
        temporary_directory = Path(directory)
        taxdump = downloads_directory / "taxdump.tar.gz"
        print("Downloading NCBI taxdump...")
        new_taxdump = download_file(NCBI_TAXDUMP_URL, taxdump)

        if not new_taxdump and (output_directory / "taxonomy.parquet").exists():
            print("NCBI formatted data is already up to date.")
            return

        print("Extracting NCBI taxdump...")
        with tarfile.open(taxdump) as archive:
            archive.extractall(temporary_directory)

        taxonomy_file = output_directory / "taxonomy.parquet"
        print("Reading NCBI taxonomy and writing taxonomy.parquet...")
        create_taxonomy_file(
            temporary_directory / "nodes.dmp",
            temporary_directory / "names.dmp",
            taxonomy_file,
        )
        print("Downloading vernacular names and writing taxon_vernacular_names.parquet...")
        create_names_file(output_directory / "taxon_vernacular_names.parquet", downloads_directory)
        print("Computing ascend and complete genome counts...")
        info = create_info_file(taxonomy_file)
        print("Downloading and reading genome reports...")
        genomes = read_genomes(download_genomes(downloads_directory))
        print("Writing taxon_info.parquet...")
        info_file = output_directory / "taxon_info.parquet"
        add_genomes(info, genomes, taxonomy_file).write_parquet(info_file)
        add_age(info_file)
        print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_directory", type=Path)
    args = parser.parse_args()
    prepare_taxonomy(args.source_directory)
