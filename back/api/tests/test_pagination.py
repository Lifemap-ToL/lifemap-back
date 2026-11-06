import httpx2

from api.lib.solr import PaginationParams, solr_fetch


async def test_full_iteration_against_real_solr(indexed_solr):
    async with httpx2.AsyncClient(base_url=indexed_solr) as client:
        ids, cursor = [], None
        while True:
            page = await solr_fetch(
                client,
                "/solr/taxo/select",
                {"q": "*:*", "fl": "id"},
                PaginationParams(page_size=100, cursor=cursor, limit=None),
            )
            ids += [d["id"] for d in page.docs]
            cursor = page.next_cursor
            if cursor is None:
                break

    assert len(ids) == 250 and len(set(ids)) == 250
    assert ids == sorted(ids)
