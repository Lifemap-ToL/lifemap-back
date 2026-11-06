"""
Taxa related routes.
"""

from collections.abc import Sequence
from typing import Annotated, Any

from fastapi import APIRouter, Path, Query
from pydantic import ConfigDict

from api.config import Settings
from api.lib.lifespan import SolrClient
from api.lib.solr import DictPage, ListPage, Pagination, solr_dict_page, solr_list_page
from api.lib.types import TaxidType, TreeName, ZoomType

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


class ScinamesMap(DictPage[str, str]):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"items": {"2": "Bacteria", "9682": "Felis"}, "next_cursor": "string", "total": 2}]
        }
    )


@router.get("/{tree}/sci_name/", response_model=ScinamesMap)
async def sci_name(
    solr_client: SolrClient,
    pg: Pagination,
    tree: Annotated[TreeName, Path(description="Tree id")],
    taxid: Annotated[list[TaxidType], Query(description="Taxid values")],
) -> DictPage[str, str]:
    """
    Route which returns the scientific names of a set of taxids as a dict.
    """

    def process_doc(doc: dict) -> tuple[str, str]:
        return str(doc["taxid"][0]), str(doc["sci_name"][0])

    params = {
        "q": "*:*",
        "fq": f"taxid:({' '.join([str(id) for id in taxid])})",
        "fl": "taxid,sci_name",
    }
    return await solr_dict_page(
        client=solr_client, path=SETTINGS.taxo_path, params=params, transform=process_doc, pg=pg
    )


@router.get("/{tree}/extent/", response_model=ListPage[dict])
async def extent(
    solr_client: SolrClient,
    pg: Pagination,
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
) -> ListPage[dict]:
    """
    Route which returns taxa located in a certain extent.
    """

    def process_doc(doc: dict) -> dict:
        return {k: flatten(v) for k, v in doc.items()}

    params = {
        "q": "*:*",
        "fq": [f"zoom:[{zoom_min} TO {zoom_max}]", f"lat:[{y_min} TO {y_max}]", f"lon:[{x_min} TO {x_max}]"],
        "fl": ",".join(fields),
    }
    return await solr_list_page(
        client=solr_client, path=SETTINGS.taxo_path, params=params, transform=process_doc, pg=pg
    )
