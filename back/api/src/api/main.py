from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import api.routes.taxa
import api.routes.tiles
from api.lib.lifespan import lifespan

app = FastAPI(
    title="Lifemap API",
    version="0.0.1",
    description="Lifemap trees and data API",
    lifespan=lifespan,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(api.routes.taxa.router)
app.include_router(api.routes.tiles.router)


@app.get("/health", tags=["utils"])
async def health() -> dict[str, str]:
    """
    Route Handler that outputs health status.
    """
    return {"status": "ok"}
