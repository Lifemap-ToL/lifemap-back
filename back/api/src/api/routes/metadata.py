"""
General tree metadata routes.
"""

import json
import pathlib
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import ConfigDict
from requests import JSONDecodeError

from api.config import Settings
from api.lib.cache import cache_for
from api.lib.types import METADATA_PATHS, TreeName

SETTINGS = Settings()

router = APIRouter(prefix="/v1/meta", tags=["metadata"])


def get_metadata_path(tree: TreeName) -> pathlib.Path:
    return METADATA_PATHS[tree]


def read_metadata(path: pathlib.Path) -> dict:
    try:
        metadata = json.loads(path.read_text())
    except FileNotFoundError, OSError, JSONDecodeError:
        raise HTTPException(502, "Problem with metadata file")
    return metadata


class UpdateMap(dict[str, str]):
    model_config = ConfigDict(json_schema_extra={"examples": [{"update": "2026-11-16"}]})


@router.get("/{tree}/update/", response_model=dict[str, str], dependencies=[Depends(cache_for(3600))])
async def tree_update(
    tree: Annotated[TreeName, Path(description="Tree id")],
    metadata_path: Annotated[pathlib.Path, Depends(get_metadata_path)],
) -> UpdateMap:
    """
    Returns update date of tree.
    """
    metadata = read_metadata(metadata_path)
    if "update" not in metadata:
        raise HTTPException(502, "Malformed metadata")
    return UpdateMap({"update": metadata["update"]})


class SpeciesMap(dict[str, dict]):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"species": {"archaea": 13843, "eukaryotes": 1862370, "bacteria": 602987, "total": 2479200}}
            ]
        }
    )


@router.get("/{tree}/species/", response_model=dict[str, dict], dependencies=[Depends(cache_for(3600))])
async def tree_species(
    tree: Annotated[TreeName, Path(description="Tree id")],
    metadata_path: Annotated[pathlib.Path, Depends(get_metadata_path)],
) -> SpeciesMap:
    """
    Returns number of species (taxa) in tree.
    """
    metadata = read_metadata(metadata_path)
    if "species" not in metadata:
        raise HTTPException(502, "Malformed metadata")
    return SpeciesMap({"species": metadata["species"]})
