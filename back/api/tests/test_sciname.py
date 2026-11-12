import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestSciname:
    url = "/v1/taxa/lifemap/sci_name/"

    def test_sciname_single(self, client: TestClient):
        with client:
            params = {"taxid": 9682}
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 1
            assert res["items"] == {"9682": "Felis"}

    def test_sciname_array(self, client: TestClient):
        with client:
            # Array of taxids
            params = {"taxid": [2, 9682]}
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 2
            assert res["items"] == {"2": "Bacteria", "9682": "Felis"}

    def test_sciname_order(self, client: TestClient):
        with client:
            # Taxids order
            params = {"taxid": [9682, 2]}
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 2
            assert res["items"] == {"2": "Bacteria", "9682": "Felis"}

    def test_sciname_duplicated(self, client: TestClient):
        with client:
            # Duplicated taxids
            params = {"taxid": [2, 9682, 9682, 2, 2]}
            response = client.get(self.url, params=params)
            assert response.status_code == 200
            res = response.json()
            assert res["total"] == 2
            assert res["items"] == {"2": "Bacteria", "9682": "Felis"}

    def test_sciname_limit(self, client: TestClient):
        with client:
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
