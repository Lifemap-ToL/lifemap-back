import time

import httpx2
import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import HttpWaitStrategy

SOLR_IMAGE = "solr:9"
CORE = "taxo"
PATH = f"/solr/{CORE}/select"
N_DOCS = 2500


@pytest.fixture(scope="session")
def solr_url():
    container = DockerContainer(SOLR_IMAGE).with_exposed_ports(8983).with_command(f"solr-precreate {CORE}")
    with container:
        container.waiting_for(HttpWaitStrategy(8983, PATH).for_status_code(200))
        container.start()
        host = container.get_container_host_ip()
        port = container.get_exposed_port(8983)
        yield f"http://{host}:{port}"


@pytest.fixture(scope="session")
def indexed_solr(solr_url):
    docs = [{"taxid": f"id_{i}", "sci_name": f"doc {i}"} for i in range(N_DOCS)]
    url = f"{solr_url}/solr/{CORE}/update?commit=true"
    for attempt in range(10):
        r = httpx2.post(url, json=docs)
        if r.status_code == 200:
            break
        if r.status_code != 503:
            r.raise_for_status()
        time.sleep(1 * (attempt + 1))
    else:
        raise AssertionError(f"Solr update kept returning 503 ({r.status_code}): {r.text}")
    return solr_url
