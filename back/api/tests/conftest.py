import httpx2
import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy


@pytest.fixture(scope="session")
def solr_url():
    container = (
        DockerContainer("solr:9")
        .with_exposed_ports(8983)
        .with_command("solr-precreate testcore")  # official image: creates a core at startup
    )
    with container:
        container.waiting_for(LogMessageWaitStrategy("Server Started"))  # adjust to what the image logs
        container.start()
        host = container.get_container_host_ip()
        port = container.get_exposed_port(8983)
        container.exec("solr create_core -c taxo")
        yield f"http://{host}:{port}"


@pytest.fixture(scope="session")
def indexed_solr(solr_url):
    docs = [{"taxid": f"{i:06d}", "sci_name": f"doc {i}"} for i in range(250)]
    r = httpx2.post(f"{solr_url}/solr/taxo/update?commit=true", json=docs)
    r.raise_for_status()
    return solr_url
