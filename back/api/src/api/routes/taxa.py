from typing import Annotated

import msgspec
from fastapi import APIRouter, Query

from api.config import Settings
from api.utils.lifespan import SolrClient
from api.utils.types import SciNameCollectionType, TaxidType, TreeName

SETTINGS = Settings()

router = APIRouter(prefix="/v1/taxa", tags=["taxa"])


@router.get("/{tree}/sci_name/")
async def sci_name(
    taxid: Annotated[list[TaxidType], Query()],
    tree: TreeName,
    solr: SolrClient,
) -> SciNameCollectionType:
    if tree == TreeName.lifemap:
        params = {
            "q": "*:*",
            "fq": f"taxid:({' '.join([str(id) for id in taxid])})",
            "wt": "json",
            "rows": 20,
            "fl": "taxid,sci_name",
        }
        r = await solr.get(SETTINGS.taxo_path, params=params)
        r.raise_for_status()
        res = msgspec.json.decode(r.content)
        return {str(d["taxid"][0]): d["sci_name"][0] for d in res["response"]["docs"]}
