import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def equal_sorted(target: list[dict], obtained: list[dict]) -> bool:
    key = lambda x: x["taxid"]
    return sorted(target, key=key) == sorted(obtained, key=key)


class TestExtent:
    url = "/v1/taxa/lifemap/extent/"

    def test_extent_base(self, client: TestClient):
        with client:
            params = {"zoom_min": 0, "zoom_max": 6, "x_min": -50, "x_max": 50, "y_min": -15, "y_max": 15}
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 3
            assert equal_sorted(
                res["items"],
                [
                    {"taxid": 2, "sci_name": "Bacteria", "zoom": 6, "lat": -11.0, "lon": 0.0},
                    {"taxid": 2157, "sci_name": "Archaea", "zoom": 6, "lat": -0.3397459999999999, "lon": 6.0},
                    {
                        "taxid": 2759,
                        "sci_name": "Eukaryota",
                        "zoom": 6,
                        "lat": -0.3397459999999999,
                        "lon": -6.0,
                    },
                ],
            )

    def test_extent_limit(self, client: TestClient):
        with client:
            params = {
                "zoom_min": 0,
                "zoom_max": 6,
                "x_min": -50,
                "x_max": 50,
                "y_min": -15,
                "y_max": 15,
                "limit": 2,
            }
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 3
            assert len(res["items"]) == 2

    def test_extent_fields(self, client: TestClient):
        with client:
            params = {
                "zoom_min": 0,
                "zoom_max": 6,
                "x_min": -50,
                "x_max": 50,
                "y_min": -15,
                "y_max": 15,
                "field": ["taxid", "zoom"],
            }
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 3
            assert equal_sorted(
                res["items"],
                [
                    {
                        "taxid": 2,
                        "zoom": 6,
                    },
                    {
                        "taxid": 2157,
                        "zoom": 6,
                    },
                    {
                        "taxid": 2759,
                        "zoom": 6,
                    },
                ],
            )

    def test_extent_lang(self, client: TestClient):
        with client:
            params = {
                "zoom_min": 0,
                "zoom_max": 6,
                "x_min": -50,
                "x_max": 50,
                "y_min": -15,
                "y_max": 15,
                "field": ["taxid", "common_name"],
                "lang": "fr",
            }
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 3
            assert equal_sorted(
                res["items"],
                [
                    {
                        "taxid": 2,
                        "common_name": "Bactéries",
                    },
                    {
                        "taxid": 2157,
                        "common_name": "Archées, Bactéries",
                    },
                    {
                        "taxid": 2759,
                    },
                ],
            )

    def test_extent_robustness(self, client: TestClient):
        with client:
            # Invalid zoom value
            params = {"zoom_min": -1, "zoom_max": 6, "x_min": -50, "x_max": 50, "y_min": -15, "y_max": 15}
            response = client.get(self.url, params=params)
            assert response.status_code == 422

            # Invalid lang
            params = {
                "lang": "invalid",
                "zoom_min": 0,
                "zoom_max": 6,
                "x_min": -50,
                "x_max": 50,
                "y_min": -15,
                "y_max": 15,
            }
            response = client.get(self.url, params=params)
            assert response.status_code == 422

            # Invalid field
            params = {
                "field": ["invalid"],
                "zoom_min": 0,
                "zoom_max": 6,
                "x_min": -50,
                "x_max": 50,
                "y_min": -15,
                "y_max": 15,
            }
            response = client.get(self.url, params=params)
            assert response.status_code == 422

            # Missing param
            params = {"zoom_min": 0, "zoom_max": 6, "x_min": -50, "x_max": 50, "y_min": -15}
            response = client.get(self.url, params=params)
            assert response.status_code == 422
