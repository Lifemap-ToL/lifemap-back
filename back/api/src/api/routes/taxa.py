"""
Taxa related routes.
"""

from typing import Annotated

import httpx2
import msgspec
from fastapi import APIRouter, HTTPException, Path, Query

from api.config import Settings
from api.utils.lifespan import SolrClient
from api.utils.types import ScinamesMap, TaxidType, TreeName

SETTINGS = Settings()

router = APIRouter(prefix="/v1/taxa", tags=["taxa"])


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
    try:
        r = await solr.get(SETTINGS.taxo_path, params=params)
        r.raise_for_status()
    except httpx2.HTTPError:
        raise HTTPException(status_code=502, detail="Upstream error")
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Upstream error")
    res = msgspec.json.decode(r.content)
    scinames_dict: dict[str, str] = {str(d["taxid"][0]): d["sci_name"][0] for d in res["response"]["docs"]}
    return ScinamesMap(scinames_dict)
