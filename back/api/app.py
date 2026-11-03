from fastapi import FastAPI

import api.routes.taxa
from api.utils.lifespan import lifespan

app = FastAPI(
    title="Lifemap API",
    version="0.0.1",
    description="Lifemap trees and data API",
    lifespan=lifespan,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url=None,
)

app.include_router(api.routes.taxa.router)


@app.get("/health")
async def health() -> dict[str, str]:
    """
    Route Handler that outputs health status.
    """
    return {"status": "ok"}
