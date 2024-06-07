import logging
from dataclasses import dataclass, field

from config import TAXO_DIRECTORY
from ete3 import Tree
from utils import get_ranks_fr, get_translations_fr

logger = logging.getLogger("LifemapBuilder")


@dataclass
class Taxid:
    sci_name: str = ""
    authority: str = ""
    synonym: str = ""
    common_name_en: list = field(default_factory=list)
    common_name_fr: list = field(default_factory=list)


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
            if tid_type == "common name":
                attr[taxid].common_name_en.append(tid_val)
            if tid_type == "scientific name":
                attr[taxid].sci_name = tid_val
                # and get translation in french (if any)
                if tid_val in taxo_fr_translations:
                    attr[taxid].common_name_fr = taxo_fr_translations[tid_val]
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
        if len(attr[tax_id].common_name_en) > 0:
            attr[tax_id].common_name_long_en = (
                "(" + ", ".join(attr[tax_id].common_name_en) + ")"
            )
            attr[tax_id].common_name_en = (
                attr[tax_id].common_name_en[0].replace("'", "''")
            )
            attr[tax_id].common_name_en = "(" + attr[tax_id].common_name_en + ")"
        else:
            attr[tax_id].common_name_en = ""
            attr[tax_id].common_name_long_en = ""

        if len(attr[tax_id].common_name_fr) > 0:
            attr[tax_id].common_name_long_fr = (
                "(" + ", ".join(attr[tax_id].common_name_fr) + ")"
            )
            attr[tax_id].common_name_fr = (
                attr[tax_id].common_name_fr[0].replace("'", "''")
            )
            attr[tax_id].common_name_fr = "(" + attr[tax_id].common_name_fr + ")"
        else:
            attr[tax_id].common_name_fr = ""
            attr[tax_id].common_name_long_fr = ""

    return attr


def getTheTrees():

    attr = get_attributes()
    ranks_fr_translations = get_ranks_fr()

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
            rank_fr = ranks_fr_translations[rank].replace("'", "''")

            if dad not in tree:
                tree[dad] = Tree()
                tree[dad].name = dad
                tree[dad].taxid = dad
                tree[dad].sci_name = attr[dad].sci_name
                tree[dad].common_name_en = attr[dad].common_name_en
                tree[dad].common_name_fr = attr[dad].common_name_fr
                tree[dad].common_name_long_en = attr[dad].common_name_long_en
                tree[dad].common_name_long_fr = attr[dad].common_name_long_fr
                tree[dad].synonym = attr[dad].synonym
                tree[dad].authority = attr[dad].authority
            if son not in tree:
                tree[son] = Tree()
                tree[son].name = son
                tree[son].rank_en = rank_en
                tree[son].rank_fr = rank_fr
                tree[son].taxid = son
                tree[son].sci_name = attr[son].sci_name
                tree[son].common_name_en = attr[son].common_name_en
                tree[son].common_name_fr = attr[son].common_name_fr
                tree[son].common_name_long_en = attr[son].common_name_long_en
                tree[son].common_name_long_fr = attr[son].common_name_long_fr
                tree[son].synonym = attr[son].synonym
                tree[son].authority = attr[son].authority
            else:
                if not hasattr(tree[son], "rank"):
                    tree[son].rank_en = rank_en
                    tree[son].rank_fr = rank_fr
            tree[dad].add_child(tree[son])
    return tree
