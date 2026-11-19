"""Build a LifeMap tree from formatted Parquet files."""

from dataclasses import dataclass, field
from pathlib import Path

import polars as pl
from config import LANG_LIST
from ete4 import Tree
from utils import get_ranks_translations


@dataclass
class Taxid:
    sci_name: str = ""
    authority: str = ""
    synonym: str = ""
    common_name: dict = field(default_factory=dict)
    common_name_long: dict = field(default_factory=dict)


def getTheTreesFromParquet(taxonomy_file: Path, names_file: Path) -> dict:
    """Build the LifeMap tree from formatted taxonomy Parquet files."""
    taxonomy = pl.read_parquet(taxonomy_file).to_dicts()
    names = pl.read_parquet(names_file).to_dicts()
    ranks_translations = get_ranks_translations()

    common_names = {}
    for row in names:
        taxon_id = row["taxon_id"]
        language = row["language"]
        name = row["name"]
        common_names.setdefault(taxon_id, {}).setdefault(language, []).append(name)

    attributes = {}
    for row in taxonomy:
        taxon_id = row["taxon_id"]
        attributes[taxon_id] = Taxid()
        attributes[taxon_id].sci_name = row["scientific_name"]
        attributes[taxon_id].authority = row["authority"]
        attributes[taxon_id].synonym = ", ".join(row["synonyms"])

        for lang in LANG_LIST:
            taxon_names = common_names.get(taxon_id, {}).get(lang, [])
            attributes[taxon_id].common_name[lang] = taxon_names

    for taxon in attributes.values():
        taxon.sci_name = taxon.sci_name.replace("'", "''")
        for lang in LANG_LIST:
            taxon_names = taxon.common_name[lang]
            taxon.common_name_long[lang] = ", ".join(taxon_names)
            if taxon_names:
                taxon.common_name[lang] = taxon_names[0].replace("'", "''")
            else:
                taxon.common_name[lang] = ""

    tree = {}
    for row in taxonomy:
        taxon_id = row["taxon_id"]
        node = Tree()
        node.props["name"] = taxon_id
        node.props["taxid"] = taxon_id
        node.props["sci_name"] = attributes[taxon_id].sci_name
        node.props["common_name"] = {}
        node.props["common_name_long"] = {}
        for lang in LANG_LIST:
            node.props["common_name"][lang] = attributes[taxon_id].common_name[lang]
            node.props["common_name_long"][lang] = attributes[taxon_id].common_name_long[lang]
        node.props["synonym"] = attributes[taxon_id].synonym
        node.props["authority"] = attributes[taxon_id].authority
        tree[taxon_id] = node

    for row in taxonomy:
        taxon_id = row["taxon_id"]
        parent_taxon_id = row["parent_taxon_id"]

        # An empty parent means that this node is the root.
        if not parent_taxon_id or taxon_id == parent_taxon_id:
            continue

        rank_names = {}
        rank = row["rank"].strip().lower()
        translated_rank = ranks_translations.get(rank, {})
        for lang in LANG_LIST:
            if lang == "en":
                rank_names[lang] = rank
            else:
                rank_names[lang] = translated_rank.get(lang, rank)
            rank_names[lang] = rank_names[lang].replace("'", "''")

        tree[taxon_id].props["rank"] = rank_names
        tree[parent_taxon_id].add_child(tree[taxon_id])

    return tree
