import os
from collections.abc import Iterator

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.application import app
from app.config import settings
from app.db.model import Base, Organization, Person, Role
from app.db.session import DatabaseSessionManager, configure_database_session_manager

from tests import utils


@pytest.fixture(scope="session")
def _aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # noqa: S105
    os.environ["AWS_SECURITY_TOKEN"] = "testing"  # noqa: S105
    os.environ["AWS_SESSION_TOKEN"] = "testing"  # noqa: S105
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="session")
def s3(_aws_credentials):
    """Return a mocked S3 client."""
    with mock_aws():
        yield boto3.client("s3")


@pytest.fixture(scope="session")
def _create_buckets(s3):
    s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)


@pytest.fixture(scope="session")
def client(_create_buckets):
    """Yield a web client instance.

    The fixture is session-scoped so that the lifespan events are executed only once per session.
    """
    with TestClient(app, headers=utils.BEARER_TOKEN) as client:
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
    db.rollback()
    query = text(f"""TRUNCATE {",".join(Base.metadata.tables)} RESTART IDENTITY CASCADE""")
    db.execute(query)
    db.commit()


@pytest.fixture
def person_id(db):
    row = Person(
        givenName="jd",
        familyName="courcol",
        pref_label="jd courcol",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row.id


@pytest.fixture
def organization_id(db):
    row = Organization(
        pref_label="ACME",
        alternative_name="A Company Making Everything",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row.id


@pytest.fixture
def role_id(db):
    row = Role(
        name="important role",
        role_id="important role id",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row.id


@pytest.fixture
def species_id(client):
    response = client.post("/species", json={"name": "Test Species", "taxonomy_id": "12345"})
    assert response.status_code == 200, f"Failed to create species: {response.text}"
    data = response.json()
    assert data["name"] == "Test Species"
    assert "id" in data, f"Failed to get id for species: {data}"
    return data["id"]


@pytest.fixture
def strain_id(client, species_id):
    response = client.post(
        "/strain",
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
        "/license",
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
    response = client.post("/brain-region", json=js)
    assert response.status_code == 200, f"Failed to create brain region: {response.text}"
    data = response.json()
    assert "id" in data, f"Failed to get id for brain region: {data}"
    return data["id"]


@pytest.fixture
def skip_project_check():
    with utils.skip_project_check():
        yield
