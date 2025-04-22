import itertools as it
import os
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

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
    MEModel,
    Organization,
    Person,
    Role,
    Species,
    Strain,
    Subject,
)
from app.db.session import DatabaseSessionManager, configure_database_session_manager
from app.dependencies import auth
from app.schemas.auth import UserContext

from . import utils
from .utils import (
    AUTH_HEADER_ADMIN,
    AUTH_HEADER_USER_1,
    AUTH_HEADER_USER_2,
    PROJECT_HEADERS,
    PROJECT_ID,
    TOKEN_ADMIN,
    TOKEN_USER_1,
    TOKEN_USER_2,
    UNRELATED_PROJECT_HEADERS,
    UNRELATED_PROJECT_ID,
    UNRELATED_VIRTUAL_LAB_ID,
    VIRTUAL_LAB_ID,
    ClientProxy,
    add_db,
)


@pytest.fixture(scope="session", autouse=True)
def _setup_env_variables():
    # Mock AWS Credentials for moto
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # noqa: S105
    os.environ["AWS_SECURITY_TOKEN"] = "testing"  # noqa: S105
    os.environ["AWS_SESSION_TOKEN"] = "testing"  # noqa: S105
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="session")
def s3():
    """Return a mocked S3 client."""
    with mock_aws():
        yield boto3.client("s3")


@pytest.fixture(scope="session")
def _create_buckets(s3):
    s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)


@pytest.fixture
def user_context_admin():
    """Admin authenticated user."""
    return UserContext(
        subject=UUID(int=1),
        email=None,
        expiration=None,
        is_authorized=True,
        is_service_admin=True,
        virtual_lab_id=None,
        project_id=None,
    )


@pytest.fixture
def user_context_user_1():
    """Admin authenticated user."""
    return UserContext(
        subject=UUID(int=1),
        email=None,
        expiration=None,
        is_authorized=True,
        is_service_admin=False,
        virtual_lab_id=VIRTUAL_LAB_ID,
        project_id=PROJECT_ID,
    )


@pytest.fixture
def user_context_user_2():
    """Regular authenticated user with different project-id."""
    return UserContext(
        subject=UUID(int=2),
        email=None,
        expiration=None,
        is_authorized=True,
        is_service_admin=False,
        virtual_lab_id=UNRELATED_VIRTUAL_LAB_ID,
        project_id=UNRELATED_PROJECT_ID,
    )


@pytest.fixture
def user_context_no_project():
    """Regular authenticated user without project-id."""
    return UserContext(
        subject=UUID(int=3),
        email=None,
        expiration=None,
        is_authorized=True,
        is_service_admin=False,
        virtual_lab_id=None,
        project_id=None,
    )


@pytest.fixture
def _override_check_user_info(
    monkeypatch,
    user_context_admin,
    user_context_user_1,
    user_context_user_2,
    user_context_no_project,
):
    # map (token, project-id) to the expected user_context
    mapping = {
        (TOKEN_ADMIN, None): user_context_admin,
        (TOKEN_USER_1, None): user_context_no_project,
        (TOKEN_USER_1, UUID(PROJECT_ID)): user_context_user_1,
        (TOKEN_USER_2, UUID(UNRELATED_PROJECT_ID)): user_context_user_2,
    }

    def mock_check_user_info(*, project_context, token, http_client):  # noqa: ARG001
        return mapping[token.credentials, project_context.project_id]

    monkeypatch.setattr(auth, "_check_user_info", mock_check_user_info)


@pytest.fixture(scope="session")
def session_client(_create_buckets):
    """Run the lifespan events.

    The fixture is session-scoped so that the lifespan events are executed only once per session.
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture
def client_no_auth(session_client, _override_check_user_info):
    """Return a web client instance, not authenticated."""
    return session_client


@pytest.fixture
def client_admin(client_no_auth):
    """Return a web client instance, authenticated as service admin without a project-id."""
    return ClientProxy(client_no_auth, headers=AUTH_HEADER_ADMIN)


@pytest.fixture
def client_user_1(client_no_auth):
    """Return a web client instance, authenticated as regular user with a specific project-id."""
    return ClientProxy(client_no_auth, headers=AUTH_HEADER_USER_1 | PROJECT_HEADERS)


@pytest.fixture
def client_user_2(client_no_auth):
    """Return a web client instance, authenticated as regular user with different project-id."""
    return ClientProxy(client_no_auth, headers=AUTH_HEADER_USER_2 | UNRELATED_PROJECT_HEADERS)


@pytest.fixture
def client_no_project(client_no_auth):
    """Return a web client instance, authenticated as regular user without a project-id."""
    return ClientProxy(client_no_auth, headers=AUTH_HEADER_USER_1)


@pytest.fixture
def client(client_user_1):
    return client_user_1


@pytest.fixture(scope="session")
def database_session_manager() -> Iterator[DatabaseSessionManager]:
    manager = configure_database_session_manager()
    yield manager
    manager.close()


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
def species_id(client_admin):
    response = client_admin.post("/species", json={"name": "Test Species", "taxonomy_id": "12345"})
    assert response.status_code == 200, f"Failed to create species: {response.text}"
    data = response.json()
    assert data["name"] == "Test Species"
    assert "id" in data, f"Failed to get id for species: {data}"
    return data["id"]


@pytest.fixture
def strain_id(client_admin, species_id):
    response = client_admin.post(
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
def subject_id(db, species_id):
    return str(
        add_db(
            db,
            Subject(
                name="my-subject",
                description="my-description",
                species_id=species_id,
                strain_id=None,
                age_value=timedelta(days=14),
                age_period="postnatal",
                sex="female",
                weight=1.5,
                authorized_public=False,
                authorized_project_id=PROJECT_ID,
            ),
        ).id
    )


@pytest.fixture
def license_id(client_admin):
    response = client_admin.post(
        "/license",
        json={
            "name": "Test License",
            "description": "a license description",
            "label": "test label",
        },
    )
    assert response.status_code == 200, f"Failed to create license: {response.text}"
    data = response.json()
    assert "id" in data, f"Failed to get id for license: {data}"
    return data["id"]


@pytest.fixture
def brain_region_id(client_admin):
    return utils.create_brain_region_id(client_admin, 64, "RedRegion")


@pytest.fixture
def morphology_id(client, species_id, strain_id, brain_region_id):
    return utils.create_reconstruction_morphology_id(
        client,
        species_id=species_id,
        strain_id=strain_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )


CreateIds = Callable[[int], list[str]]


@pytest.fixture
def agents(db: Session):
    organization_1 = add_db(
        db, Organization(pref_label="test_organization_1", alternative_name="alt name 1")
    )
    person_1 = add_db(
        db, Person(pref_label="test_person_1", givenName="given name 1", familyName="family name 1")
    )
    role = add_db(db, Role(role_id=1, name="test role"))

    return organization_1, person_1, role


def add_contributions(db: Session, agents: tuple[Agent, Agent, Role], entity_id: uuid.UUID):
    agent_1, agent_2, role = agents
    add_db(db, Contribution(agent_id=agent_1.id, role_id=role.id, entity_id=entity_id))
    add_db(db, Contribution(agent_id=agent_2.id, role_id=role.id, entity_id=entity_id))


@pytest.fixture
def create_emodel_ids(
    db, morphology_id, brain_region_id, species_id, strain_id, agents
) -> CreateIds:
    def _create_emodels(count: int):
        emodel_ids: list[str] = []
        for i in range(count):
            emodel_id = add_db(
                db,
                EModel(
                    name=f"{i}",
                    description=f"{i}_description",
                    brain_region_id=brain_region_id,
                    species_id=species_id,
                    strain_id=strain_id,
                    exemplar_morphology_id=morphology_id,
                    authorized_public=False,
                    authorized_project_id=PROJECT_ID,
                ),
            ).id

            add_contributions(db, agents, emodel_id)

            emodel_ids.append(str(emodel_id))

        return emodel_ids

    return _create_emodels


@pytest.fixture
def emodel_id(create_emodel_ids: CreateIds) -> str:
    return create_emodel_ids(1)[0]


@pytest.fixture
def create_memodel_ids(
    db, morphology_id, brain_region_id, species_id, strain_id, emodel_id, agents
) -> CreateIds:
    def _create_memodel_ids(count: int):
        memodel_ids: list[str] = []
        for i in range(count):
            memodel_id = add_db(
                db,
                MEModel(
                    name=f"{i}",
                    description=f"{i}_description",
                    brain_region_id=brain_region_id,
                    species_id=species_id,
                    strain_id=strain_id,
                    morphology_id=morphology_id,
                    emodel_id=emodel_id,
                    authorized_public=False,
                    authorized_project_id=PROJECT_ID,
                ),
            ).id

            add_contributions(db, agents, memodel_id)

            memodel_ids.append(str(memodel_id))

        return memodel_ids

    return _create_memodel_ids


@pytest.fixture
def memodel_id(create_memodel_ids: CreateIds) -> str:
    return create_memodel_ids(1)[0]


class EModelIds(BaseModel):
    emodel_ids: list[str]
    species_ids: list[str]
    brain_region_ids: list[int]
    morphology_ids: list[str]


@dataclass
class MEModels:
    memodels: list[MEModel]
    species_ids: list[str]
    brain_region_ids: list[int]
    morphology_ids: list[str]
    emodel_ids: list[str]
    agent_ids: list[str]


@pytest.fixture
def faceted_emodel_ids(db: Session, client, client_admin):
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
    brain_region_ids = [
        utils.create_brain_region_id(client_admin, i, f"region{i}") for i in range(2)
    ]

    morphology_ids = [
        str(
            utils.create_reconstruction_morphology_id(
                client,
                species_id=species_ids[i],
                strain_id=strain_ids[i],
                brain_region_id=brain_region_ids[i],
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
        emodel_id = add_db(
            db,
            EModel(
                name="",
                description=f"species{species_id}, brain_region{brain_region_id}, ex_morphology{morphology_id}",  # noqa: E501
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=None,
                exemplar_morphology_id=morphology_id,
                authorized_public=False,
                authorized_project_id=PROJECT_ID,
            ),
        ).id

        emodel_ids.append(str(emodel_id))

    return EModelIds(
        emodel_ids=emodel_ids,
        species_ids=species_ids,
        brain_region_ids=brain_region_ids,
        morphology_ids=morphology_ids,
    )


@pytest.fixture
def faceted_memodels(
    db: Session, client: TestClient, client_admin: TestClient, agents: tuple[Agent, Agent, Role]
):
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
    brain_region_ids = [
        utils.create_brain_region_id(client_admin, i, f"region{i}") for i in range(2)
    ]

    morphology_ids = [
        str(
            utils.create_reconstruction_morphology_id(
                client,
                species_id=species_ids[i],
                strain_id=strain_ids[i],
                brain_region_id=brain_region_ids[i],
                authorized_public=False,
                name=f"test morphology {i}",
            )
        )
        for i in range(2)
    ]

    emodel_ids = [
        str(
            add_db(
                db,
                EModel(
                    name=f"{i}",
                    brain_region_id=brain_region_ids[i],
                    species_id=species_ids[i],
                    exemplar_morphology_id=morphology_ids[i],
                    authorized_public=False,
                    authorized_project_id=PROJECT_ID,
                ),
            ).id
        )
        for i in range(2)
    ]

    agent_ids = [str(agents[0].id), str(agents[1].id)]

    memodels = []

    for species_id, brain_region_id, morphology_id, emodel_id in it.product(
        species_ids, brain_region_ids, morphology_ids, emodel_ids
    ):
        memodel = add_db(
            db,
            MEModel(
                name="",
                description="foo" if species_id == species_ids[0] else "bar",
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=None,
                morphology_id=morphology_id,
                emodel_id=emodel_id,
                authorized_public=False,
                authorized_project_id=PROJECT_ID,
            ),
        )

        add_contributions(db, agents, memodel.id)

        memodels.append(memodel)

    return MEModels(
        memodels=memodels,
        emodel_ids=emodel_ids,
        morphology_ids=morphology_ids,
        species_ids=species_ids,
        brain_region_ids=brain_region_ids,
        agent_ids=agent_ids,
    )
