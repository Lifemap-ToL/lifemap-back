from enum import Enum
from typing import Annotated

import httpx2
import msgspec
from fastapi import Depends, FastAPI, Query
from fastapi.openapi.utils import get_openapi
from pydantic import PositiveInt

SOLR_URL = "http://localhost:8983/solr/taxo/select"


SciNameCollectionType = dict[str, str]

TaxidType = Annotated[PositiveInt, Query(lt=1e9)]


class TreeName(str, Enum):
    lifemap = "lifemap"


# Dependency to get the HTTP client
async def get_solr_client():
    async with httpx2.AsyncClient(
        timeout=httpx2.Timeout(5.0, connect=1.0),
        limits=httpx2.Limits(max_connections=100, max_keepalive_connections=50),
        headers={"Accept-Encoding": "identity"},
    ) as client:
        yield client


async def lifespan(app: FastAPI):
    # Store the HTTP client in app state
    app.state.solr = httpx2.AsyncClient(
        timeout=httpx2.Timeout(5.0, connect=1.0),
        limits=httpx2.Limits(max_connections=100, max_keepalive_connections=50),
        headers={"Accept-Encoding": "identity"},
    )
    try:
        yield
    finally:
        await app.state.solr.aclose()


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Lifemap API",
        version="0.0.1",
        description="Lifemap trees and data API",
        routes=app.routes,
    )
    # You can modify the schema here if needed
    return openapi_schema


app = FastAPI(lifespan=lifespan, openapi_url="/openapi.json", docs_url="/docs", redoc_url=None)


@app.get("/v1/taxon/sci_name/")
async def sci_name(
    taxid: Annotated[list[TaxidType], Query()], solr: Annotated[httpx2.AsyncClient, Depends(get_solr_client)]
) -> SciNameCollectionType:
    params = {
        "q": "*:*",
        "fq": f"taxid:({' '.join([str(id) for id in taxid])})",
        "wt": "json",
        "rows": 20,
        "fl": "taxid,sci_name",
    }
    r = await solr.get(SOLR_URL, params=params)
    r.raise_for_status()
    res = msgspec.json.decode(r.content)
    return {str(d["taxid"][0]): d["sci_name"][0] for d in res["response"]["docs"]}


@app.get("/hello")
async def sync_hello_world() -> dict[str, str]:
    """Route Handler that outputs hello world."""
    return {"hello": "world!"}
