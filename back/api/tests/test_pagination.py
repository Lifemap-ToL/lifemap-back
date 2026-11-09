import httpx2
import pytest
from conftest import N_DOCS, PATH
from fastapi import FastAPI, HTTPException

from api.lib.lifespan import get_solr_client
from api.lib.solr import (
    DictPage,
    ListPage,
    Pagination,
    PaginationParams,
    SolrClient,
    decode_cursor,
    encode_cursor,
    solr_dict_page,
    solr_fetch,
    solr_list_page,
)

PARAMS = {"q": "*:*", "fl": "taxid,sci_name", "sort": "id asc"}


@pytest.fixture
async def api(indexed_solr):
    async with httpx2.AsyncClient(base_url=indexed_solr, timeout=30) as solr:
        app = FastAPI()

        @app.get("/documents", response_model=ListPage[dict])
        async def list_docs(pg: Pagination, solr: SolrClient) -> ListPage[dict]:
            return await solr_list_page(
                solr,
                PATH,
                PARAMS,
                pg,
                transform=lambda d: {"taxid": d["taxid"][0], "sci_name": d["sci_name"][0]},
            )

        @app.get("/names", response_model=DictPage[str, str])
        async def names(pg: Pagination, solr: SolrClient) -> DictPage[str, str]:
            return await solr_dict_page(
                solr, PATH, PARAMS, pg, transform=lambda d: (d["taxid"][0], d["sci_name"][0])
            )

        app.dependency_overrides[get_solr_client] = lambda: solr
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client


async def iterate(api, url, **params):
    pages, cursor = [], None
    first_call = True
    while True:
        if not first_call and "limit" in params:
            del params["limit"]
        q = {**params, **({"cursor": cursor} if cursor else {})}
        r = await api.get(url, params=q)
        assert r.status_code == 200, r.text
        body = r.json()
        pages.append(body)
        cursor = body["next_cursor"]
        first_call = False
        if not cursor:
            return pages


class TestCursor:
    def test_cursor_roundtrip(self):
        assert decode_cursor(encode_cursor("AoE/abc+def=", 150)) == ("AoE/abc+def=", 150)
        assert decode_cursor(encode_cursor("*", None)) == ("*", None)

    def test_cursor_is_url_safe(self):
        # Solr marks can contain + / = ; the wrapper must not
        c = encode_cursor("a+b/c==", 1)
        assert not set(c) & set("+/ ")

    @pytest.mark.parametrize("invalid_cursor", ["", "not-base64!!", "e30="])
    def test_decode_invalid_cursor(self, invalid_cursor):
        with pytest.raises(HTTPException) as exc:
            decode_cursor(invalid_cursor)
        assert exc.value.status_code == 400


class TestPagination:
    async def test_full_iteration_against_real_solr(self, indexed_solr):
        async with httpx2.AsyncClient(base_url=indexed_solr) as client:
            ids, cursor = [], None
            while True:
                page = await solr_fetch(
                    client,
                    PATH,
                    {"q": "*:*", "fl": "id"},
                    PaginationParams(page_size=100, cursor=cursor, limit=None),
                )
                ids += [d["id"] for d in page.docs]
                cursor = page.next_cursor
                if cursor is None:
                    break

        assert len(ids) == N_DOCS and len(set(ids)) == N_DOCS
        assert ids == sorted(ids)

    async def test_defaults(self, api):
        body = (await api.get("/documents")).json()
        # The route's default page_size is 1000.
        assert len(body["items"]) == min(1000, N_DOCS)
        assert body["next_cursor"] and body["total"] == N_DOCS

    async def test_full_iteration_over_http(self, api):
        pages = await iterate(api, "/documents", page_size=1000)
        ids = [d["taxid"] for p in pages for d in p["items"]]

        assert len(ids) == N_DOCS and len(set(ids)) == N_DOCS
        # Items are transformed to taxid/sci_name only.
        assert set(pages[0]["items"][0]) == {"taxid", "sci_name"}

    async def test_limit_over_http(self, api):
        pages = await iterate(api, "/documents", page_size=400, limit=1500)
        assert sum(len(p["items"]) for p in pages) == 1500

    @pytest.mark.parametrize("size", [0, -1, 50001])
    async def test_page_size_out_of_bounds_is_422(self, api, size):
        assert (await api.get("/documents", params={"page_size": size})).status_code == 422

    async def test_cursor_and_limit_together_is_400(self, api):
        first = (await api.get("/documents")).json()
        r = await api.get("/documents", params={"cursor": first["next_cursor"], "limit": 10})
        assert r.status_code == 400

    @pytest.mark.parametrize("cursor", ["###", "e30="])
    async def test_invalid_cursor_is_400(self, api, cursor):
        assert (await api.get("/documents", params={"cursor": cursor})).status_code == 400

    async def test_mapping_route(self, api):
        pages = await iterate(api, "/names", page_size=1000)
        merged = {}
        for p in pages:
            merged |= p["items"]

        assert len(merged) == N_DOCS and merged["id_7"] == "doc 7"
        assert pages[0]["total"] == N_DOCS and pages[1]["total"] is None

    async def test_openapi_exposes_pagination_parameters(self, api):
        spec = (await api.get("/openapi.json")).json()
        names = {p["name"] for p in spec["paths"]["/documents"]["get"]["parameters"]}
        assert {"page_size", "cursor", "limit"} <= names
