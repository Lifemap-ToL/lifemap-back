import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routes.metadata import get_metadata_path


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def metadata_file(tmp_path) -> Path:
    f = tmp_path / "metadata.json"
    f.write_text(
        json.dumps(
            {
                "update": "2026-11-16",
                "species": {"archaea": 13843, "eukaryotes": 1862370, "bacteria": 602987, "total": 2479200},
            }
        )
    )
    return f


class TestMetadataUpdate:
    url = "/v1/meta/lifemap/update/"

    def test_update(self, client, metadata_file):
        app.dependency_overrides[get_metadata_path] = lambda: metadata_file
        response = client.get(self.url)
        assert response.status_code == 200
        assert response.json() == {"update": "2026-11-16"}

    def test_update_invalid(self, client):
        app.dependency_overrides[get_metadata_path] = lambda: Path("invalid.json")
        response = client.get(self.url)
        assert response.status_code == 502


class TestMetadataSpecies:
    url = "/v1/meta/lifemap/species/"

    def test_update(self, client, metadata_file):
        app.dependency_overrides[get_metadata_path] = lambda: metadata_file
        response = client.get(self.url)
        assert response.status_code == 200
        assert response.json() == {
            "species": {"archaea": 13843, "eukaryotes": 1862370, "bacteria": 602987, "total": 2479200}
        }

    def test_update_invalid(self, client):
        app.dependency_overrides[get_metadata_path] = lambda: Path("invalid.json")
        response = client.get(self.url)
        assert response.status_code == 502
