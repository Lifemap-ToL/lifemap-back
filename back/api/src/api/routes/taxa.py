"""
Taxa related routes.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path, Query
from pydantic import ConfigDict

from api.config import Settings
from api.lib.cache import cache_for
from api.lib.fields import TaxoFieldType, fields_param
from api.lib.lifespan import SolrClient
from api.lib.pagination import ListPage, Pagination, solr_list_page
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


class TaxidsList(ListPage[dict[str, Any]]):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "items": [{"taxid": "2", "sci_name": "Bacteria"}, {"taxid": "9682", "sci_name": "Felis"}],
                    "next_cursor": "string",
                    "total": 2,
                }
            ]
        }
    )


async def get_taxids_page(
    solr_client: SolrClient,
    pg: Pagination,
    taxid: list[TaxidType],
    field: list[str],
) -> ListPage[dict]:
    params = {
        "q": "*:*",
        "fq": f"taxid:({' '.join(str(id) for id in taxid)})",
        "fl": ",".join(field),
    }

    def process_doc(doc: dict) -> dict:
        return {k: flatten(v) for k, v in doc.items()}

    return await solr_list_page(
        client=solr_client,
        path=SETTINGS.taxo_path,
        params=params,
        transform=process_doc,
        pg=pg,
    )


@router.get(
    "/{tree}/taxids/",
    response_model=TaxidsList,
    dependencies=[Depends(cache_for(3600))],
    summary="Taxonomic data for a set of taxids (GET)",
)
async def taxids_get(
    solr_client: SolrClient,
    pg: Pagination,
    tree: Annotated[TreeName, Path(description="Tree id")],
    taxid: Annotated[list[TaxidType], Query(description="Taxid values")],
    field: Annotated[list[str], Depends(fields_param([TaxoFieldType.taxid, TaxoFieldType.sci_name]))],
) -> ListPage[dict]:
    """
    Returns a set of taxonomic field values for a set of taxids.

    As it uses GET method, the number of taxids is limited by the maximum size of a URL.
    Use the POST route instead if you have a great number of taxids to query.
    """
    return await get_taxids_page(solr_client, pg, taxid, field)


@router.post(
    "/{tree}/taxids/",
    response_model=TaxidsList,
    summary="Taxonomic data for a set of taxids (POST)",
)
async def taxids_post(
    solr_client: SolrClient,
    pg: Pagination,
    tree: Annotated[TreeName, Path(description="Tree id")],
    taxid: Annotated[list[TaxidType], Body(description="Taxid values")],
    field: Annotated[
        list[str], Depends(fields_param([TaxoFieldType.taxid, TaxoFieldType.sci_name], source="body"))
    ],
) -> ListPage[dict]:
    """
    Returns a set of taxonomic field values for a set of taxids.

    Suitable for a large number of taxids.
    """
    return await get_taxids_page(solr_client, pg, taxid, field)


@router.get(
    "/{tree}/extent/",
    response_model=ListPage[dict],
    dependencies=[Depends(cache_for(3600))],
    summary="Get taxids in a given spatial extent",
)
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
    field: Annotated[
        list[TaxoFieldType],
        Depends(
            fields_param(
                [
                    TaxoFieldType.taxid,
                    TaxoFieldType.sci_name,
                    TaxoFieldType.zoom,
                    TaxoFieldType.lat,
                    TaxoFieldType.lon,
                ]
            )
        ),
    ],
) -> ListPage[dict]:
    """
    Returns taxonomic field values for taxa located in a certain spatial extent.

    The extent is defined by minimum and maximum x, y and zoom values.
    """

    def process_doc(doc: dict) -> dict:
        return {k: flatten(v) for k, v in doc.items()}

    params = {
        "q": "*:*",
        "fq": [f"zoom:[{zoom_min} TO {zoom_max}]", f"lat:[{y_min} TO {y_max}]", f"lon:[{x_min} TO {x_max}]"],
        "fl": ",".join(field),
    }
    return await solr_list_page(
        client=solr_client, path=SETTINGS.taxo_path, params=params, transform=process_doc, pg=pg
    )
