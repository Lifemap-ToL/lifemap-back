"""
Tiles related routes.
"""

from typing import Annotated

import httpx2
from fastapi import APIRouter, HTTPException, Path

from api.config import Settings
from api.lib.lifespan import BboxClient
from api.lib.types import ProtobufResponse, TilesType, TreeName, XYType, ZoomType

SETTINGS = Settings()

router = APIRouter(prefix="/v1/tiles", tags=["tiles"])


@router.get(
    "/{tree}/{type}/{z}/{x}/{y}.pbf",
    response_class=ProtobufResponse,
    responses={
        200: {
            "description": "Mapbox Vector Tile",
            "content": {"application/x-protobuf": {"schema": {"type": "string", "format": "binary"}}},
        },
        204: {"description": "Empty tile"},
        502: {"description": "Upstream error"},
    },
)
async def vector_tiles(
    tree: Annotated[TreeName, Path(description="Tree id")],
    type: Annotated[TilesType, Path(description="Tiles type")],
    x: Annotated[XYType, Path(description="Tile x coordinate")],
    y: Annotated[XYType, Path(description="Tile y coordinate")],
    z: Annotated[ZoomType, Path(description="Tile zoom level")],
    bbox: BboxClient,
) -> ProtobufResponse:
    """
    Route which returns a Mapbox vector tile (MVT) as a protobuf binary.
    """

    tile_url: str = f"/xyz/composite/{z}/{x}/{y}.pbf"
    try:
        r = await bbox.get(tile_url)
        r.raise_for_status()
    except httpx2.HTTPError:
        raise HTTPException(status_code=502, detail="Upstream error")
    if r.status_code == 404:
        return ProtobufResponse(status_code=204)  # empty tile
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Upstream error")
    return ProtobufResponse(
        content=r.content,
        headers={"Cache-Control": "public, max-age=3600"},
    )
