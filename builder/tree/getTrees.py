import logging
from dataclasses import dataclass, field

from config import LANG_LIST, TAXO_DIRECTORY
from ete4 import Tree
from utils import get_ranks_translations, get_translations_fr

logger = logging.getLogger("LifemapBuilder")


@dataclass
class Taxid:
    sci_name: str = ""
    authority: str = ""
    synonym: str = ""
    common_name: dict = field(default_factory=dict)
    common_name_long: dict = field(default_factory=dict)


def get_attributes() -> dict:
    """
    List attributes of each species per taxid

    Returns
    -------
    dict
        attributes dictionary.
    """

    logger.info("Reading NCBI taxonomy...")

    taxo_fr_translations = get_translations_fr()

    attr = {}  ##here we will list attribute of each species per taxid
    with open(TAXO_DIRECTORY / "names.dmp") as f:
        for line in f:
            taxid = line.split("|")[0].replace("\t", "")
            tid_val = line.split("|")[1].replace("\t", "")
            tid_type = line.split("|")[3].replace("\t", "")
            if taxid not in attr:
                attr[taxid] = Taxid()
                for lang in LANG_LIST:
                    attr[taxid].common_name[lang] = []
            if tid_type == "common name":
                attr[taxid].common_name["en"].append(tid_val)
            if taxid in taxo_fr_translations:
                attr[taxid].common_name["fr"] = taxo_fr_translations[taxid]
            if tid_type == "scientific name":
                attr[taxid].sci_name = tid_val
                # and get translation in french (if any)
            if tid_type == "authority":
                if attr[taxid].authority != "":
                    attr[taxid].authority = attr[taxid].authority + ", " + tid_val
                else:
                    attr[taxid].authority = tid_val
            if tid_type == "synonym":
                if attr[taxid].synonym != "":
                    attr[taxid].synonym = attr[taxid].synonym + ", " + tid_val
                else:
                    attr[taxid].synonym = tid_val

    for tax_id in attr:
        attr[tax_id].sci_name = attr[tax_id].sci_name.replace("'", "''")
        for lang in LANG_LIST:
            if len(attr[tax_id].common_name[lang]) > 0:
                common_name_long = ", ".join(attr[tax_id].common_name[lang])
                attr[tax_id].common_name_long[lang] = f"{common_name_long}"
                common_name = next(iter(attr[tax_id].common_name[lang]))
                attr[tax_id].common_name[lang] = f"{common_name.replace("'", "''")}"
            else:
                attr[tax_id].common_name[lang] = ""
                attr[tax_id].common_name_long[lang] = ""

    return attr


def getTheTrees() -> dict:
    attr = get_attributes()
    ranks_translations = get_ranks_translations()

    tree = {}

    logger.info("Building the NCBI taxonomy tree...")

    filepath = TAXO_DIRECTORY / "nodes.dmp"
    with open(filepath) as fp:
        _ = fp.readline()  ## remove the 1 | 1 edge
        for line in fp:
            line = line.split("|")
            dad = line[1].replace("\t", "")
            son = line[0].replace("\t", "")
            rank = line[2].replace("\t", "")
            rank_en = rank.replace("'", "''")
            rank_fr = ranks_translations[rank]["fr"].replace("'", "''")

            if dad not in tree:
                tree[dad] = Tree()
                tree[dad].props["name"] = dad
                tree[dad].props["taxid"] = dad
                tree[dad].props["sci_name"] = attr[dad].sci_name
                tree[dad].props["common_name"] = {}
                tree[dad].props["common_name_long"] = {}
                for lang in LANG_LIST:
                    tree[dad].props["common_name"][lang] = attr[dad].common_name[lang]
                    tree[dad].props["common_name_long"][lang] = attr[dad].common_name_long[lang]
                tree[dad].props["synonym"] = attr[dad].synonym
                tree[dad].props["authority"] = attr[dad].authority
            if son not in tree:
                tree[son] = Tree()
                tree[son].props["name"] = son
                tree[son].props["taxid"] = son
                tree[son].props["sci_name"] = attr[son].sci_name
                tree[son].props["common_name"] = {}
                tree[son].props["common_name_long"] = {}
                tree[son].props["rank"] = {}
                tree[son].props["rank"]["en"] = rank_en
                tree[son].props["rank"]["fr"] = rank_fr
                for lang in LANG_LIST:
                    tree[son].props["common_name"][lang] = attr[son].common_name[lang]
                    tree[son].props["common_name_long"][lang] = attr[son].common_name_long[lang]
                tree[son].props["synonym"] = attr[son].synonym
                tree[son].props["authority"] = attr[son].authority
            else:
                if "rank" not in tree[son].props:
                    tree[son].props["rank"] = {}
                    tree[son].props["rank"]["en"] = rank_en
                    tree[son].props["rank"]["fr"] = rank_fr
            tree[dad].add_child(tree[son])
    return tree
