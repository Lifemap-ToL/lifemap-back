"""
Suggester (autocompletion) related routes.
"""

import re
from typing import Annotated

import httpx2
import msgspec
from fastapi import APIRouter, HTTPException, Path, Query

from api.config import Settings
from api.lib.lifespan import SolrClient
from api.lib.types import LangType, TreeName

SETTINGS = Settings()

router = APIRouter(prefix="/v1/suggest", tags=["suggest"])


@router.get("/{tree}/{lang}/", response_model=list[dict[str, str]])
async def suggest(
    solr_client: SolrClient,
    tree: Annotated[TreeName, Path(description="Tree id")],
    lang: Annotated[LangType, Path(description="Suggestions language")],
    search: Annotated[str, Query(description="Text to search for taxa suggestions")],
    remove_markup: Annotated[bool, Query(description="Wether to keep bold markup added by Solr")] = True,
    n: Annotated[int, Query(ge=1, le=15, description="Number of suggestions to fetch")] = 10,
) -> list[dict[str, str]]:
    """
    Route which returns taxa suggestions from a string.
    """

    params = {
        "suggest.q": search,
        "wt": "json",
        "rows": 1,
    }

    try:
        r = await solr_client.get(SETTINGS.suggester_path[lang], params=params)
        # Cursor pagination error
        if r.status_code == 400:
            raise HTTPException(400, "Invalid query or cursor")
        r.raise_for_status()
    except httpx2.HTTPError:
        raise HTTPException(status_code=502, detail="Upstream error")
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Upstream error")
    res = msgspec.json.decode(r.content)

    suggestions = res["suggest"][SETTINGS.suggester_name[lang]][search]["suggestions"]
    suggestions = [[t.strip() for t in s["term"].split("|")] for s in suggestions[0:n]]
    suggestions = [
        {
            "sci_name": s[0],
            "common_name": s[1],
            "rank": s[2],
            "taxid": s[3],
        }
        for s in suggestions
    ]
    if remove_markup:
        suggestions = [{k: re.sub(r"</?b>", "", v) for k, v in s.items()} for s in suggestions]

    return suggestions
