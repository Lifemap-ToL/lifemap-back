import base64
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, overload

import httpx2
import msgspec
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel
from requests import JSONDecodeError

from api.lib.lifespan import SolrClient

# --- PAGINATION ---


class PaginationParams(BaseModel):
    page_size: int
    cursor: str | None
    limit: int | None


def pagination_params(
    page_size: int = Query(1000, ge=1, le=50000),
    cursor: str | None = Query(None, description="Opaque cursor from a previous response"),
    limit: int | None = Query(None, ge=1, description="Maximum number of rows to retrieve (first call only)"),
) -> PaginationParams:
    if cursor and limit:
        raise HTTPException(400, "limit can only be set on the first call")
    return PaginationParams(page_size=page_size, cursor=cursor, limit=limit)


Pagination = Annotated[PaginationParams, Depends(pagination_params)]


def encode_cursor(mark: str, remaining: int | None) -> str:
    """
    Encode both Solr next cursor mark and computed number of remaining results
    as URL safe base64.
    """
    raw = json.dumps({"m": mark, "r": remaining}).encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_cursor(cursor: str) -> tuple[str, int | None]:
    """
    Decode Solr next cursor mark and number of remaining results
    from URL safe base64.
    """
    try:
        d = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        return d["m"], d["r"]
    except ValueError, JSONDecodeError:
        raise HTTPException(400, "Invalid cursor")


@dataclass
class RawPage:
    docs: list[dict]
    next_cursor: str | None
    total: int | None


async def solr_fetch(
    client: SolrClient,
    path: str,
    params: dict,
    pg: PaginationParams,
    transform: Callable[[dict], Any] | None = None,
) -> RawPage:
    """
    Function handling Solr query and results pagination.
    """

    # Default mark and remaining value at first page
    mark, remaining = ("*", pg.limit)
    # Get mark and remaining values for next pages
    if pg.cursor:
        mark, remaining = decode_cursor(pg.cursor)

    # Number of rows is either page size or the number of remaining rows
    rows = pg.page_size if remaining is None else min(pg.page_size, remaining)
    query = {
        **params,
        "rows": rows,
        "cursorMark": mark,
        # Sort by id for cursor pagination
        "sort": "id asc",
        "wt": "json",
    }
    try:
        r = await client.get(path, params=query)
        # Cursor pagination error
        if r.status_code == 400:
            raise HTTPException(400, "Invalid query or cursor")
        r.raise_for_status()
    except httpx2.HTTPError:
        raise HTTPException(status_code=502, detail="Upstream error")
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Upstream error")
    res = msgspec.json.decode(r.content)

    docs = res["response"]["docs"]
    n_docs = len(docs)
    next_mark = res["nextCursorMark"]
    # If remaining is defined (limit on first page or computed remaining results on next pages)
    # actualise it
    if remaining is not None:
        remaining -= n_docs

    # Apply transform
    if transform:
        docs = [d for d in map(transform, docs) if d is not None]

    done = n_docs == 0 or next_mark == mark or (remaining is not None and remaining <= 0)
    return RawPage(
        docs=docs,
        next_cursor=None if done else encode_cursor(next_mark, remaining),
        # Incude total only on first page
        total=res["response"]["numFound"] if pg.cursor is None else None,
    )


# --- Pagination for list results ----


class ListPage[T](BaseModel):
    items: list[T]
    next_cursor: str | None = None
    total: int | None = None  # only on the first page


@overload
async def solr_list_page(
    client: SolrClient,
    path: str,
    params: dict,
    pg: PaginationParams,
) -> ListPage[dict]:
    """
    solr_list_page overload when transform is not passed
    """


@overload
async def solr_list_page[T](
    client: SolrClient,
    path: str,
    params: dict,
    pg: PaginationParams,
    transform: Callable[[dict], T],
) -> ListPage[T]:
    """
    solr_list_page overload when a transform is passed returning generic type T
    """


async def solr_list_page(
    client: SolrClient,
    path: str,
    params: dict,
    pg: PaginationParams,
    transform: Callable[[dict], Any] | None = None,
) -> ListPage[Any]:
    """
    Fetch Solr query results and returns a paginated list
    """
    raw = await solr_fetch(client, path, params, pg)
    items = [transform(d) for d in raw.docs] if transform else raw.docs
    return ListPage(items=items, next_cursor=raw.next_cursor, total=raw.total)


# --- Pagination for dictionary results ----


class DictPage[K, V](BaseModel):
    items: dict[K, V]
    next_cursor: str | None = None
    total: int | None = None


async def solr_dict_page[K, V](
    client: SolrClient,
    path: str,
    params: dict,
    pg: PaginationParams,
    transform: Callable[[dict], tuple[K, V]],
) -> DictPage[K, V]:
    """
    Fetch Solr query results and returns a paginated dict
    """
    raw = await solr_fetch(client, path, params, pg)
    items = dict(transform(d) for d in raw.docs)
    return DictPage(items=items, next_cursor=raw.next_cursor, total=raw.total)
