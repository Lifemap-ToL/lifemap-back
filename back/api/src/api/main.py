import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import api.routes.metadata
import api.routes.suggesters
import api.routes.taxa
import api.routes.tiles
from api.lib.lifespan import lifespan

app = FastAPI(
    title="Lifemap API",
    version="0.0.1",
    description=Path("README.md").read_text(encoding="utf-8"),
    lifespan=lifespan,
    root_path="/" if os.getenv("FASTAPI_ENV") == "development" else "/api",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Don't add CORS middleware in production as it is handled by the
# web server
if os.getenv("FASTAPI_ENV") == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )


app.include_router(api.routes.metadata.router)
app.include_router(api.routes.suggesters.router)
app.include_router(api.routes.taxa.router)
app.include_router(api.routes.tiles.router)
