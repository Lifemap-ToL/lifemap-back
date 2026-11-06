import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestSciname:
    url = "/v1/taxa/lifemap/sci_name/"

    def test_sciname(self, client: TestClient):
        with client:
            # Single taxid
            params = {"taxid": 9682}
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 1
            assert res["items"] == {"9682": "Felis"}

            # Array of taxids
            params = {"taxid": [2, 9682]}
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 2
            assert res["items"] == {"2": "Bacteria", "9682": "Felis"}

            # Taxids order
            params = {"taxid": [9682, 2]}
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 2
            assert res["items"] == {"2": "Bacteria", "9682": "Felis"}

            # Duplicated taxids
            params = {"taxid": [2, 9682, 9682, 2, 2]}
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 2
            assert res["items"] == {"2": "Bacteria", "9682": "Felis"}

            # Limit
            params = {"taxid": [2, 9682], "limit": 1}
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 2
            assert res["items"] == {"2": "Bacteria"}

    def test_sciname_robustness(self, client: TestClient):
        with client:
            # Invalid taxid
            params = {"taxid": -1}
            response = client.get(self.url, params=params)
            assert response.status_code == 422

            # Non existent taxid
            params = {"taxid": 999999999}
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 0
            assert res["items"] == {}


def equal_sorted(target: list[dict], obtained: list[dict]) -> bool:
    key = lambda x: x["taxid"]
    return sorted(target, key=key) == sorted(obtained, key=key)


class TestExtent:
    url = "/v1/taxa/lifemap/extent/"

    def test_extent(self, client: TestClient):
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

            # Limit
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
            assert equal_sorted(
                res["items"],
                [
                    {"taxid": 2, "sci_name": "Bacteria", "zoom": 6, "lat": -11.0, "lon": 0.0},
                    {
                        "taxid": 2759,
                        "sci_name": "Eukaryota",
                        "zoom": 6,
                        "lat": -0.3397459999999999,
                        "lon": -6.0,
                    },
                ],
            )

            # Custom fields
            params = {
                "zoom_min": 0,
                "zoom_max": 6,
                "x_min": -50,
                "x_max": 50,
                "y_min": -15,
                "y_max": 15,
                "fields": ["taxid", "zoom"],
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

    def test_extent_robustness(self, client: TestClient):
        with client:
            # Invalid zoom value
            params = {"zoom_min": -1, "zoom_max": 6, "x_min": -50, "x_max": 50, "y_min": -15, "y_max": 15}
            response = client.get(self.url, params=params)
            assert response.status_code == 422

            # Missing param
            params = {"zoom_min": 0, "zoom_max": 6, "x_min": -50, "x_max": 50, "y_min": -15}
            response = client.get(self.url, params=params)
            assert response.status_code == 422
