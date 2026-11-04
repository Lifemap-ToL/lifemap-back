import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestSciname:
    url = "/v1/tiles/lifemap/composite"

    def test_sciname(self, client: TestClient):
        with client:
            tile_url = f"{self.url}/4/0/8.pbf"
            response = client.get(tile_url)
            assert response.status_code == 200

    def test_sciname_robustness(self, client: TestClient):
        with client:
            # Invalid zoom level
            tile_url = f"{self.url}/400/0/8.pbf"
            response = client.get(tile_url)
            assert response.status_code == 422

            # Invalid x value
            tile_url = f"{self.url}/4/-1/8.pbf"
            response = client.get(tile_url)
            assert response.status_code == 422

            # Non-existent tile
            tile_url = f"{self.url}/4/0/800.pbf"
            response = client.get(tile_url)
            assert response.status_code == 502
