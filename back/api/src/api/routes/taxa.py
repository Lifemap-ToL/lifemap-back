"""
Taxa related routes.
"""

from collections.abc import Sequence
from typing import Annotated, Any

from fastapi import APIRouter, Path, Query

from api.config import Settings
from api.lib.lifespan import SolrClient
from api.lib.solr import solr_query
from api.lib.types import ScinamesMap, TaxidType, TreeName, ZoomType

SETTINGS = Settings()

router = APIRouter(prefix="/v1/taxa", tags=["taxa"])


def flatten(x: Any) -> Any:
    """
    Utility function to convert any one element list to the element value.

    Parameters
    ----------
    x : Any
        Value to flatten.

    Returns
    -------
    Any
        x[0] if x is a list of length 1, otherwise x


    """
    return x[0] if isinstance(x, list) and len(x) == 1 else x


@router.get("/{tree}/sci_name/")
async def sci_name(
    tree: Annotated[TreeName, Path(description="Tree id")],
    taxid: Annotated[list[TaxidType], Query(description="Taxid values")],
    solr: SolrClient,
) -> ScinamesMap:
    """
    Route which returns the scientific names of a set of taxids as a dict.
    """

    params = {
        "q": "*:*",
        "fq": f"taxid:({' '.join([str(id) for id in taxid])})",
        "wt": "json",
        "rows": 20,
        "fl": "taxid,sci_name",
    }
    res = await solr_query(SETTINGS.taxo_path, params=params, solr=solr)
    scinames_dict: dict[str, str] = {str(d["taxid"][0]): d["sci_name"][0] for d in res["response"]["docs"]}
    return ScinamesMap(scinames_dict)


@router.get("/{tree}/extent/")
async def extent(
    solr: SolrClient,
    tree: Annotated[TreeName, Path(description="Tree id")],
    x_min: Annotated[float, Query(description="Minimum x coordinates (longitude)")],
    x_max: Annotated[float, Query(description="Maximum x coordinates (longitude)")],
    y_min: Annotated[float, Query(description="Minimum y coordinates (latitude)")],
    y_max: Annotated[float, Query(description="Maximum y coordinates (latitude)")],
    zoom_min: Annotated[ZoomType, Query(description="Minimum zoom level")],
    zoom_max: Annotated[ZoomType, Query(description="Maximum zoom level")],
    fields: Annotated[Sequence[str], Query(description="Fields to retrieve for each taxon")] = (
        "taxid",
        "lon",
        "lat",
        "zoom",
        "sci_name",
    ),
):
    """
    Route which returns taxa located in a certain extent.
    """

    params = {
        "q": "*:*",
        "fq": [f"zoom:[{zoom_min} TO {zoom_max}]", f"lat:[{y_min} TO {y_max}]", f"lon:[{x_min} TO {x_max}]"],
        "wt": "json",
        "rows": 1000,
        "fl": ",".join(fields),
    }
    res = await solr_query(SETTINGS.taxo_path, params=params, solr=solr)
    docs = [doc for doc in res["response"]["docs"]]
    docs = [{k: flatten(v) for k, v in doc.items()} for doc in docs]
    return docs
