import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestSuggest:
    url_en = "/v1/suggest/lifemap/en/"
    url_fr = "/v1/suggest/lifemap/fr/"
    url_de = "/v1/suggest/lifemap/de/"
    url_es = "/v1/suggest/lifemap/es/"
    url_el = "/v1/suggest/lifemap/el/"
    url_bad_lang = "/v1/suggest/lifemap/invalid_lang/"
    url_bad_tree = "/v1/suggest/invalid_tree/en/"

    def test_suggest(self, client: TestClient):
        with client:
            params = {"search": "small cats"}
            response = client.get(self.url_en, params=params)
            assert response.status_code == 200
            res = response.json()
            assert len(res) == 6
            assert res[0]["taxid"] == "9682"

            params = {"search": "chat"}
            response = client.get(self.url_fr, params=params)
            assert response.status_code == 200
            res = response.json()
            assert len(res) == 10
            assert res[0]["taxid"] == "9682"

            params = {"search": "katze"}
            response = client.get(self.url_de, params=params)
            assert response.status_code == 200
            res = response.json()
            assert len(res) == 10
            assert res[0]["taxid"] == "9682"

            params = {"search": "gatos"}
            response = client.get(self.url_es, params=params)
            assert response.status_code == 200
            res = response.json()
            assert len(res) == 6
            assert res[0]["taxid"] == "9682"

            params = {"search": "Γάτα"}
            response = client.get(self.url_el, params=params)
            assert response.status_code == 200
            res = response.json()
            assert len(res) == 9
            assert res[0]["taxid"] == "9682"

    def test_suggest_n(self, client: TestClient):
        with client:
            params = {"search": "small cats", "n": 3}
            response = client.get(self.url_en, params=params)
            assert response.status_code == 200
            res = response.json()
            assert len(res) == 3

    def test_suggest_robustness(self, client: TestClient):
        with client:
            # Invalid lang
            params = {"search": "homo"}
            response = client.get(self.url_bad_lang, params=params)
            assert response.status_code == 422

            # Invalid tree
            params = {"search": "homo"}
            response = client.get(self.url_bad_tree, params=params)
            assert response.status_code == 422

            # Invalid n
            params = {"search": "homo", "n": 0}
            response = client.get(self.url_en, params=params)
            assert response.status_code == 422
            params = {"search": "homo", "n": 16}
            response = client.get(self.url_en, params=params)
            assert response.status_code == 422
