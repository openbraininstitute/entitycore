from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.application import app
from app.db.model import Base
from app.db.session import DatabaseSessionManager, configure_database_session_manager


@pytest.fixture(scope="session")
def client():
    """Yield a web client instance.

    The fixture is session-scoped so that the lifespan events are executed only once per session.
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def database_session_manager() -> DatabaseSessionManager:
    return configure_database_session_manager()


@pytest.fixture
def db(database_session_manager) -> Iterator[Session]:
    with database_session_manager.session() as session:
        yield session


@pytest.fixture(autouse=True)
def _db_cleanup(db):
    yield
    query = text(f"""TRUNCATE {",".join(Base.metadata.tables)} RESTART IDENTITY CASCADE""")
    db.execute(query)
    db.commit()


@pytest.fixture
def species_id(client):
    response = client.post("/species/", json={"name": "Test Species", "taxonomy_id": "12345"})
    assert response.status_code == 200, f"Failed to create species: {response.text}"
    data = response.json()
    assert data["name"] == "Test Species"
    assert "id" in data, f"Failed to get id for species: {data}"
    return data["id"]


@pytest.fixture
def strain_id(client, species_id):
    response = client.post(
        "/strain/",
        json={
            "name": "Test Strain",
            "taxonomy_id": "Taxonomy ID",
            "species_id": species_id,
        },
    )
    assert response.status_code == 200, f"Failed to create strain: {response.text}"
    data = response.json()
    assert data["taxonomy_id"] == "Taxonomy ID"
    assert "id" in data, f"Failed to get id for strain: {data}"
    return data["id"]


@pytest.fixture
def license_id(client):
    response = client.post(
        "/license/",
        json={
            "name": "Test License",
            "description": "a license description",
            "label": "test label",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data, f"Failed to get id for license: {data}"
    return data["id"]


@pytest.fixture
def brain_region_id(client):
    js = {
        "id": 64,
        "acronym": "red",
        "name": "RedRegion",
        "color_hex_triplet": "FF0000",
        "children": [],
    }
    response = client.post("/brain-region/", json=js)
    assert response.status_code == 200, f"Failed to create brain region: {response.text}"
    data = response.json()
    assert "id" in data, f"Failed to get id for brain region: {data}"
    return data["id"]
