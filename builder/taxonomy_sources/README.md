# Taxonomy sources

This directory contains source-specific converters. Each converter should
produce the same normalized Parquet files, regardless of the original source.

The NCBI converter downloads NCBI taxdump data and vernacular names from
`taxonomy-all`.

It also downloads the NCBI genome reports and stores the number of complete
genomes, including descendant genomes, as `genomes` in `taxon_info.parquet`.
Downloaded NCBI files are kept in the source's `downloads/` directory and are
reused when they are still current.

The Catalogue of Life converter reads `NameUsage.tsv` and `VernacularName.tsv`
from a CoL EX zip file.

The common names file contains only `taxon_id`, `language`, and `name`. The
current LifeMap backend does not use name types or preferred-name flags.

The WoRMS converter reads `taxon.txt`. Accepted WoRMS nodes become taxonomy
rows, while other names linked to an accepted node become synonyms. WoRMS does
not provide vernacular names in this export, so its names file is empty. The
common WoRMS LSID prefix is removed from identifiers, leaving values such as
`1` and `2`.

The GBIF converter reads `Taxon.tsv` and `VernacularName.tsv` from a GBIF
Backbone zip file. GBIF has several top-level taxa, so the converter adds a
single root with the identifier `-1` and attaches those taxa to it.

The ITIS converter reads the `ITIS.sqlite` database from the ITIS zip file.
It uses the ITIS hierarchy, synonym links, authorities, ranks, and vernacular
names to create the common Parquet files. ITIS uses `0` as the synthetic root
parent, so the converter adds a root taxon with identifier `0`.

The OTT converter reads `taxonomy.tsv` and `synonyms.tsv` from an OTT archive.
OTT does not provide vernacular names in this export, so its vernacular names
file is empty. OTT source information, unique names, and flags are kept in
`taxon_info.parquet`.

The generated files should be written under:

```text
data/taxonomy_datasets/ncbi/
```

Run it with:

```bash
python3 builder/taxonomy_sources/prepare_ncbi.py data/taxonomy_datasets/ncbi
```

For a Catalogue of Life EX export:

```bash
python3 builder/taxonomy_sources/prepare_col.py \
  data/taxonomy_datasets/catalogue_of_life
```

For a WoRMS export:

```bash
python3 builder/taxonomy_sources/prepare_worms.py \
  data/taxonomy_datasets/worms
```

For a GBIF Backbone export:

```bash
python3 builder/taxonomy_sources/prepare_gbif.py \
  data/taxonomy_datasets/gbif
```

For an ITIS export:

```bash
python3 builder/taxonomy_sources/prepare_itis.py \
  data/taxonomy_datasets/itis
```

For an OTT export:

```bash
python3 builder/taxonomy_sources/prepare_ott.py \
  data/taxonomy_datasets/ott
```
