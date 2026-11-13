import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def equal_sorted(target: list[dict], obtained: list[dict]) -> bool:
    key = lambda x: x["taxid"]
    return sorted(target, key=key) == sorted(obtained, key=key)


class TestTaxids:
    url = "/v1/taxa/lifemap/taxids/"

    def test_taxids_get(self, client: TestClient):
        with client:
            params = {"taxid": [2, 9682]}
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 2
            assert equal_sorted(
                res["items"],
                [{"taxid": 2, "sci_name": "Bacteria"}, {"taxid": 9682, "sci_name": "Felis"}],
            )

    def test_taxids_post(self, client: TestClient):
        with client:
            params = {"taxid": [2, 9682]}
            response = client.post(self.url, json=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 2
            assert equal_sorted(
                res["items"],
                [{"taxid": 2, "sci_name": "Bacteria"}, {"taxid": 9682, "sci_name": "Felis"}],
            )

    def test_taxids_limit(self, client: TestClient):
        with client:
            params = {
                "taxid": [2, 9682],
                "limit": 1,
            }
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 2
            assert len(res["items"]) == 1

    def test_taxids_duplicated(self, client: TestClient):
        with client:
            params = {
                "taxid": [2, 9682, 9682, 2],
            }
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 2
            assert len(res["items"]) == 2

    def test_taxids_fields(self, client: TestClient):
        with client:
            params = {
                "taxid": [2, 9682],
                "field": ["zoom"],
            }
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 2
            assert equal_sorted(
                res["items"],
                [
                    {
                        "taxid": 2,
                        "zoom": 6,
                    },
                    {
                        "taxid": 9682,
                        "zoom": 25,
                    },
                ],
            )

    def test_taxids_fields_post(self, client: TestClient):
        with client:
            params = {
                "taxid": [2, 9682],
                "field": ["zoom"],
            }
            response = client.post(self.url, json=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 2
            assert equal_sorted(
                res["items"],
                [
                    {
                        "taxid": 2,
                        "zoom": 6,
                    },
                    {
                        "taxid": 9682,
                        "zoom": 25,
                    },
                ],
            )

    def test_taxids_lang(self, client: TestClient):
        with client:
            params = {"taxid": [2, 9682], "field": ["taxid", "rank"], "lang": "fr"}
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 2
            assert equal_sorted(
                res["items"],
                [
                    {
                        "taxid": 2,
                        "rank": "domaine",
                    },
                    {
                        "taxid": 9682,
                        "rank": "genre",
                    },
                ],
            )

    def test_taxids_lang_post(self, client: TestClient):
        with client:
            params = {"taxid": [2, 9682], "field": ["taxid", "rank"], "lang": "fr"}
            response = client.post(self.url, json=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 2
            assert equal_sorted(
                res["items"],
                [
                    {
                        "taxid": 2,
                        "rank": "domaine",
                    },
                    {
                        "taxid": 9682,
                        "rank": "genre",
                    },
                ],
            )

    def test_taxids_robustness(self, client: TestClient):
        with client:
            # Invalid taxid value
            params = {"taxid": [-1]}
            response = client.get(self.url, params=params)
            assert response.status_code == 422

            # Invalid lang
            params = {"taxid": [2, 9682], "lang": "invalid"}
            response = client.get(self.url, params=params)
            assert response.status_code == 422

            # Invalid fields
            params = {
                "taxid": [2, 9682],
                "field": ["invalid"],
            }
            response = client.get(self.url, params=params)
            assert response.status_code == 422

            # Missing param
            params = {}
            response = client.get(self.url, params=params)
            assert response.status_code == 422
