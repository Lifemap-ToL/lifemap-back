import httpx2
import msgspec
from fastapi import HTTPException

from api.lib.lifespan import SolrClient


async def solr_query(path: str, params: dict, solr: SolrClient) -> dict:
    try:
        r = await solr.get(path, params=params)
        print(r.url)
        r.raise_for_status()
    except httpx2.HTTPError:
        raise HTTPException(status_code=502, detail="Upstream error")
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Upstream error")
    res = msgspec.json.decode(r.content)
    return res
