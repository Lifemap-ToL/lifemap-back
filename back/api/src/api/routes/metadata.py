"""
General tree metadata routes.
"""

import json
import pathlib
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, ConfigDict
from requests import JSONDecodeError

from api.config import Settings
from api.lib.cache import cache_for
from api.lib.lifespan import BboxClient, SolrClient
from api.lib.types import TreeName

SETTINGS = Settings()

router = APIRouter(prefix="/v1/meta", tags=["metadata"])


def get_metadata_path(tree: TreeName) -> pathlib.Path:
    return SETTINGS.metadata_path[tree]


def read_metadata(path: pathlib.Path) -> dict:
    try:
        metadata = json.loads(path.read_text())
    except FileNotFoundError, OSError, JSONDecodeError:
        raise HTTPException(502, "Problem with metadata file")
    return metadata


class UpdateMap(BaseModel):
    update: str
    model_config = ConfigDict(json_schema_extra={"examples": [{"update": "2026-11-16"}]})


@router.get("/{tree}/update/", dependencies=[Depends(cache_for(3600))], summary="Date of last tree update")
async def tree_update(
    tree: Annotated[TreeName, Path(description="Tree id")],
    metadata_path: Annotated[pathlib.Path, Depends(get_metadata_path)],
) -> UpdateMap:
    """
    Returns the date of the last update of a tree.
    """
    metadata = read_metadata(metadata_path)
    if "update" not in metadata:
        raise HTTPException(502, "Malformed metadata")
    return UpdateMap(update=metadata["update"])


class SpeciesMap(BaseModel):
    species: dict[str, int]
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"species": {"archaea": 13843, "eukaryotes": 1862370, "bacteria": 602987, "total": 2479200}}
            ]
        }
    )


@router.get("/{tree}/species/", dependencies=[Depends(cache_for(3600))], summary="Species count of a tree")
async def tree_species(
    tree: Annotated[TreeName, Path(description="Tree id")],
    metadata_path: Annotated[pathlib.Path, Depends(get_metadata_path)],
) -> SpeciesMap:
    """
    Returns the number of species (taxa) in a tree.
    """
    metadata = read_metadata(metadata_path)
    if "species" not in metadata:
        raise HTTPException(502, "Malformed metadata")
    return SpeciesMap(species=metadata["species"])


class HealthMap(BaseModel):
    data: Literal["OK", "ERROR"]
    tiles: Literal["OK", "ERROR"]
    metadata: Literal["OK", "ERROR"]
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"data": "OK", "tiles": "OK", "metadata": "ERROR"}]}
    )


@router.get(
    "/{tree}/health/", dependencies=[Depends(cache_for(3600))], summary="Technical health status of a tree"
)
async def tree_health(
    tree: Annotated[TreeName, Path(description="Tree id")],
    metadata_path: Annotated[pathlib.Path, Depends(get_metadata_path)],
    solr: SolrClient,
    bbox: BboxClient,
) -> HealthMap:
    """
    Returns health status (online availability) of the different components of a tree:
    metadata, taxonomic data, and tiles.
    """

    # Metadata
    metadata = "OK"
    try:
        _ = read_metadata(metadata_path)
    except HTTPException:
        metadata = "ERROR"

    # Vector tiles
    tiles = "OK"
    try:
        r = await bbox.get("/health")
        r.raise_for_status()
    except HTTPException:
        tiles = "ERROR"
    if r.status_code != 200 or r.text != "OK":
        tiles = "ERROR"

    # Solr data
    data = "OK"
    try:
        r = await solr.get("/")
        r.raise_for_status()
    except HTTPException:
        data = "ERROR"
    if r.status_code != 200:
        data = "ERROR"

    return HealthMap(data=data, tiles=tiles, metadata=metadata)
