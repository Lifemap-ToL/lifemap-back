from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

import httpx2
from fastapi import Depends, FastAPI, Request

from api.config import Settings

SETTINGS = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    async with httpx2.AsyncClient(
        base_url=SETTINGS.solr_url,
        timeout=httpx2.Timeout(5.0, connect=1.0),
        limits=httpx2.Limits(max_connections=100, max_keepalive_connections=50),
        headers={"Accept-Encoding": "identity"},
    ) as solr_client:
        app.state.solr_client = solr_client
        yield


def get_solr_client(request: Request) -> httpx2.AsyncClient:
    return request.app.state.solr_client


SolrClient = Annotated[httpx2.AsyncClient, Depends(get_solr_client)]
