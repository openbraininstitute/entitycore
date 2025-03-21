import itertools as it
import os
from collections.abc import Iterator

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.application import app
from app.config import settings
from app.db.model import (
    Agent,
    Base,
    Contribution,
    EModel,
    Organization,
    Person,
    Role,
    Species,
    Strain,
)
from app.db.session import DatabaseSessionManager, configure_database_session_manager

from .utils import PROJECT_HEADERS, PROJECT_ID, add_db
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


def create_brain_region_id(client: TestClient, id_: int, name: str):
    js = {
        "id": id_,
        "acronym": f"acronym{id_}",
        "name": name,
        "color_hex_triplet": "FF0000",
        "children": [],
    }
    response = client.post("/brain-region", json=js)
    assert response.status_code == 200, f"Failed to create brain region: {response.text}"
    data = response.json()
    assert "id" in data, f"Failed to get id for brain region: {data}"
    return data["id"]


@pytest.fixture
def brain_region_id(client):
    return create_brain_region_id(client, 64, "RedRegion")


@pytest.fixture
def exemplar_morphology_id(client, species_id, strain_id, brain_region_id, skip_project_check):  # noqa: ARG001
    return utils.create_reconstruction_morphology_id(
        client,
        species_id,
        strain_id,
        brain_region_id,
        utils.PROJECT_HEADERS | utils.BEARER_TOKEN,
        authorized_public=False,
    )


def create_emodel_id(
    db,
    species_id,
    strain_id,
    brain_region_id,
    exemplar_morphology_id,
    authorized_project_id,
    authorized_public,
    name="Test Emodel Name",
    description="Test Emodel Description",
):
    return add_db(
        db,
        EModel(
            name=name,
            description=description,
            brain_region_id=brain_region_id,
            species_id=species_id,
            strain_id=strain_id,
            exemplar_morphology_id=exemplar_morphology_id,
            authorized_public=authorized_public,
            authorized_project_id=authorized_project_id,
            iteration="1",
            score=-1,
            seed=-1,
        ),
    ).id


@pytest.fixture
def create_emodel_ids(db, exemplar_morphology_id, brain_region_id, species_id, strain_id):
    agent_1 = add_db(db, Agent(pref_label="test_agent_1"))
    agent_2 = add_db(db, Agent(pref_label="test_agent_2"))
    role = add_db(db, Role(role_id=1, name="test role"))

    def add_contributions(emodel_id: int):
        add_db(db, Contribution(agent_id=agent_1.id, role_id=role.id, entity_id=emodel_id))
        add_db(db, Contribution(agent_id=agent_2.id, role_id=role.id, entity_id=emodel_id))

    def _create_emodels(count: int):
        emodel_ids = []
        for i in range(count):
            emodel_id = create_emodel_id(
                db,
                species_id,
                strain_id,
                brain_region_id,
                authorized_project_id=PROJECT_ID,
                authorized_public=False,
                name=f"{i}",
                description=f"{i}_description",
                exemplar_morphology_id=exemplar_morphology_id,
            )

            add_contributions(emodel_id)

            emodel_ids.append(emodel_id)

        return emodel_ids

    return _create_emodels


class Ids(BaseModel):
    emodel_ids: list[str]
    species_ids: list[str]
    brain_region_ids: list[int]
    morphology_ids: list[str]


@pytest.fixture
def create_faceted_emodel_ids(db: Session, client: TestClient):
    species_ids = [
        str(add_db(db, Species(name=f"TestSpecies{i}", taxonomy_id=f"{i}")).id) for i in range(2)
    ]

    strain_ids = [
        str(
            add_db(
                db, Strain(name=f"TestStrain{i}", taxonomy_id=f"{i + 2}", species_id=species_ids[i])
            ).id
        )
        for i in range(2)
    ]
    brain_region_ids = [create_brain_region_id(client, i, f"region{i}") for i in range(2)]

    morphology_ids = [
        str(
            utils.create_reconstruction_morphology_id(
                client,
                species_id=species_ids[i],
                strain_id=strain_ids[i],
                brain_region_id=brain_region_ids[i],
                headers=PROJECT_HEADERS,
                authorized_public=False,
                name=f"test exemplar morphology {i}",
            )
        )
        for i in range(2)
    ]

    emodel_ids = []
    for species_id, brain_region_id, morphology_id in it.product(
        species_ids, brain_region_ids, morphology_ids
    ):
        emodel_id = str(
            create_emodel_id(
                db,
                species_id,
                strain_id=None,
                brain_region_id=brain_region_id,
                authorized_project_id=PROJECT_ID,
                authorized_public=False,
                name="",
                description=f"species{species_id}, brain_region{brain_region_id}, ex_morphology{morphology_id}",  # noqa: E501
                exemplar_morphology_id=morphology_id,
            )
        )
        emodel_ids.append(emodel_id)

    return Ids(
        emodel_ids=emodel_ids,
        species_ids=species_ids,
        brain_region_ids=brain_region_ids,
        morphology_ids=morphology_ids,
    )


@pytest.fixture
def skip_project_check():
    with utils.skip_project_check():
        yield
