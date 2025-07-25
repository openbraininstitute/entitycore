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
from app.config import storages
from app.db.model import (
    Agent,
    Base,
    BrainAtlas,
    Circuit,
    Contribution,
    EModel,
    ETypeClass,
    ETypeClassification,
    MEModel,
    MTypeClass,
    MTypeClassification,
    Organization,
    Publication,
    ReconstructionMorphology,
    Role,
    Simulation,
    SimulationCampaign,
    SimulationResult,
    Species,
    Strain,
    Subject,
)
from app.db.session import DatabaseSessionManager, configure_database_session_manager
from app.db.types import StorageType
from app.dependencies import auth
from app.schemas.auth import UserContext, UserProfile

from . import utils
from .utils import (
    ADMIN_SUB_ID,
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
    USER_SUB_ID_1,
    USER_SUB_ID_2,
    VIRTUAL_LAB_ID,
    ClientProxy,
    add_db,
    assert_request,
    create_electrical_cell_recording_id_with_assets,
)


@pytest.fixture(scope="session", autouse=True)
def _setup_env_variables():
    # Mock AWS Credentials for moto
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # noqa: S105
    os.environ["AWS_SECURITY_TOKEN"] = "testing"  # noqa: S105
    os.environ["AWS_SESSION_TOKEN"] = "testing"  # noqa: S105


@pytest.fixture(scope="session")
def s3():
    """Return a mocked S3 client."""
    with mock_aws():
        yield boto3.client("s3")


@pytest.fixture(scope="session")
def _create_buckets(s3):
    s3.create_bucket(Bucket=storages[StorageType.aws_s3_internal].bucket)
    s3.create_bucket(Bucket=storages[StorageType.aws_s3_open].bucket, ACL="public-read")


@pytest.fixture
def user_context_admin():
    """Admin authenticated user."""
    return UserContext(
        profile=UserProfile(
            subject=UUID(ADMIN_SUB_ID),
            name="Admin User",
        ),
        expiration=None,
        is_authorized=True,
        is_service_admin=True,
        virtual_lab_id=None,
        project_id=None,
    )


@pytest.fixture
def user_context_user_1():
    """Regular authenticated user with project-id."""
    return UserContext(
        profile=UserProfile(
            subject=UUID(USER_SUB_ID_1),
            name="Regular User With Project Id",
        ),
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
        profile=UserProfile(
            subject=UUID(USER_SUB_ID_2),
            name="Regular User With Different Project Id",
        ),
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
        profile=UserProfile(
            subject=UUID(int=3),
            name="Regular User Without Project Id",
        ),
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
    return utils.create_person(
        db,
        given_name="jd",
        family_name="courcol",
        pref_label="jd courcol",
        sub_id=USER_SUB_ID_1,
    ).id


@pytest.fixture
def organization_id(db, person_id):
    row = Organization(
        pref_label="ACME",
        alternative_name="A Company Making Everything",
        created_by_id=person_id,
        updated_by_id=person_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row.id


@pytest.fixture
def role_id(db, person_id):
    row = Role(
        name="important role",
        role_id="important role id",
        created_by_id=person_id,
        updated_by_id=person_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row.id


@pytest.fixture
def species_id(client_admin, person_id):
    response = client_admin.post(
        "/species",
        json={
            "name": "Test Species",
            "taxonomy_id": "12345",
            "created_by_id": str(person_id),
            "updated_by_id": str(person_id),
        },
    )
    assert response.status_code == 200, f"Failed to create species: {response.text}"
    data = response.json()
    assert data["name"] == "Test Species"
    assert "id" in data, f"Failed to get id for species: {data}"
    return data["id"]


@pytest.fixture
def strain_id(client_admin, species_id, person_id):
    response = client_admin.post(
        "/strain",
        json={
            "name": "Test Strain",
            "taxonomy_id": "Taxonomy ID",
            "species_id": species_id,
            "created_by_id": str(person_id),
            "updated_by_id": str(person_id),
        },
    )
    assert response.status_code == 200, f"Failed to create strain: {response.text}"
    data = response.json()
    assert data["taxonomy_id"] == "Taxonomy ID"
    assert "id" in data, f"Failed to get id for strain: {data}"
    return data["id"]


@pytest.fixture
def subject_id(db, species_id, person_id):
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
                created_by_id=str(person_id),
                updated_by_id=str(person_id),
            ),
        ).id
    )


@pytest.fixture
def license_id(client_admin, person_id):
    response = client_admin.post(
        "/license",
        json={
            "name": "Test License",
            "description": "a license description",
            "label": "test label",
            "created_by_id": str(person_id),
            "updated_by_id": str(person_id),
        },
    )
    assert response.status_code == 200, f"Failed to create license: {response.text}"
    data = response.json()
    assert "id" in data, f"Failed to get id for license: {data}"
    return data["id"]


@pytest.fixture
def brain_region_hierarchy_id(db, person_id):
    return utils.create_hiearchy_name(db, "AIBS", created_by_id=person_id).id


@pytest.fixture
def brain_region_id(db, brain_region_hierarchy_id, person_id):
    return str(
        utils.create_brain_region(
            db, brain_region_hierarchy_id, 64, "RedRegion", created_by_id=person_id
        ).id
    )


@pytest.fixture
def brain_atlas_id(db, brain_region_hierarchy_id, person_id, species_id):
    return add_db(
        db,
        BrainAtlas(
            name="test brain atlas",
            description="test brain atlas description",
            species_id=species_id,
            hierarchy_id=brain_region_hierarchy_id,
            authorized_project_id=PROJECT_ID,
            authorized_public=False,
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    ).id


@pytest.fixture
def morphology_id(db, client, species_id, strain_id, brain_region_id, person_id):
    model_id = utils.create_reconstruction_morphology_id(
        client,
        species_id=species_id,
        strain_id=strain_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )
    mtype = add_db(
        db,
        MTypeClass(
            pref_label="m1",
            alt_label="m1",
            definition="m1d",
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )
    add_db(
        db,
        MTypeClassification(
            entity_id=model_id,
            mtype_class_id=mtype.id,
            created_by_id=person_id,
            updated_by_id=person_id,
            authorized_public=False,
            authorized_project_id=PROJECT_ID,
        ),
    )
    return model_id


@pytest.fixture
def mtype_class_id(db, person_id):
    return str(
        add_db(
            db,
            MTypeClass(
                pref_label="mtype-pref-label",
                alt_label="mtype-alt-label",
                definition="mtype-definition",
                created_by_id=str(person_id),
                updated_by_id=str(person_id),
            ),
        ).id
    )


@pytest.fixture
def validation_result_id(client, morphology_id, person_id):
    return assert_request(
        client.post,
        url="/validation-result",
        json={
            "name": "test_validation_result",
            "passed": True,
            "validated_entity_id": str(morphology_id),
            "authorized_public": False,
            "created_by_id": str(person_id),
            "updated_by_id": str(person_id),
        },
    ).json()["id"]


@pytest.fixture
def memodel_calibration_result_id(client, memodel_id):
    return assert_request(
        client.post,
        url="/memodel-calibration-result",
        json={
            "name": "test_memodel_calibration_result",
            "calibrated_entity_id": str(memodel_id),
            "authorized_public": False,
            "threshold_current": 0.8,
            "holding_current": 0.2,
            "rin": 100.0,  # Optional field, can be None
        },
    ).json()["id"]


CreateIds = Callable[[int], list[str]]


@pytest.fixture
def agents(db: Session, person_id):
    organization_1 = add_db(
        db,
        Organization(
            pref_label="test_organization_1",
            alternative_name="alt name 1",
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )
    person_1 = utils.create_person(
        db,
        pref_label="test_person_1",
        given_name="given name 1",
        family_name="family name 1",
        created_by_id=person_id,
    )
    role = add_db(
        db, Role(role_id=1, name="test role", created_by_id=person_id, updated_by_id=person_id)
    )

    return organization_1, person_1, role


def add_contributions(db: Session, agents: tuple[Agent, Agent, Role], entity_id: uuid.UUID):
    agent_1, agent_2, role = agents
    add_db(
        db,
        Contribution(
            agent_id=agent_1.id,
            role_id=role.id,
            entity_id=entity_id,
            created_by_id=agent_2.id,
            updated_by_id=agent_2.id,
        ),
    )
    add_db(
        db,
        Contribution(
            agent_id=agent_2.id,
            role_id=role.id,
            entity_id=entity_id,
            created_by_id=agent_2.id,
            updated_by_id=agent_2.id,
        ),
    )


@pytest.fixture
def create_emodel_ids(
    client, db, morphology_id, brain_region_id, species_id, strain_id, agents, person_id
) -> CreateIds:
    def _create_emodels(count: int):
        emodel_ids: list[str] = []
        for i in range(count):
            emodel_id = assert_request(
                client.post,
                url="/emodel",
                json={
                    "name": f"{i}",
                    "brain_region_id": str(brain_region_id),
                    "description": f"{i}_description",
                    "species_id": str(species_id),
                    "strain_id": str(strain_id),
                    "iteration": "test iteration",
                    "score": 10 * i,
                    "seed": -1,
                    "exemplar_morphology_id": str(morphology_id),
                    "authorized_public": False,
                },
            ).json()["id"]

            add_contributions(db, agents, emodel_id)

            # create a unique etype for each emodel
            etype = add_db(
                db,
                ETypeClass(
                    pref_label=f"e1-{emodel_id}",
                    alt_label=f"e1-{emodel_id}",
                    definition="e1d",
                    created_by_id=person_id,
                    updated_by_id=person_id,
                ),
            )
            add_db(
                db,
                ETypeClassification(
                    entity_id=emodel_id,
                    etype_class_id=etype.id,
                    created_by_id=person_id,
                    updated_by_id=person_id,
                    authorized_public=False,
                    authorized_project_id=PROJECT_ID,
                ),
            )

            emodel_ids.append(str(emodel_id))

        return emodel_ids

    return _create_emodels


@pytest.fixture
def emodel_id(create_emodel_ids: CreateIds) -> str:
    return create_emodel_ids(1)[0]


@pytest.fixture
def create_memodel_ids(
    db, morphology_id, brain_region_id, species_id, strain_id, emodel_id, agents, person_id
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
                    created_by_id=person_id,
                    updated_by_id=person_id,
                ),
            ).id

            add_contributions(db, agents, memodel_id)

            emodel = db.get(EModel, emodel_id)
            morphology = db.get(ReconstructionMorphology, morphology_id)

            add_db(
                db,
                MTypeClassification(
                    entity_id=memodel_id,
                    mtype_class_id=morphology.mtypes[0].id,
                    created_by_id=person_id,
                    updated_by_id=person_id,
                    authorized_public=False,
                    authorized_project_id=PROJECT_ID,
                ),
            )
            add_db(
                db,
                ETypeClassification(
                    entity_id=memodel_id,
                    etype_class_id=emodel.etypes[0].id,
                    created_by_id=person_id,
                    updated_by_id=person_id,
                    authorized_public=False,
                    authorized_project_id=PROJECT_ID,
                ),
            )

            memodel_ids.append(str(memodel_id))

        return memodel_ids

    return _create_memodel_ids


@pytest.fixture
def memodel_id(create_memodel_ids: CreateIds) -> str:
    return create_memodel_ids(1)[0]


class EModelIds(BaseModel):
    emodel_ids: list[str]
    species_ids: list[str]
    brain_region_ids: list[uuid.UUID]
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
def faceted_emodel_ids(db: Session, client, person_id):
    species_ids = [
        str(
            add_db(
                db,
                Species(
                    name=f"TestSpecies{i}",
                    taxonomy_id=f"{i}",
                    created_by_id=person_id,
                    updated_by_id=person_id,
                ),
            ).id
        )
        for i in range(2)
    ]

    strain_ids = [
        str(
            add_db(
                db,
                Strain(
                    name=f"TestStrain{i}",
                    taxonomy_id=f"{i + 2}",
                    species_id=species_ids[i],
                    created_by_id=person_id,
                    updated_by_id=person_id,
                ),
            ).id
        )
        for i in range(2)
    ]
    hierarchy_name = utils.create_hiearchy_name(db, "test_hier", created_by_id=person_id)
    brain_region_ids = [
        utils.create_brain_region(
            db, hierarchy_name.id, i, f"region{i}", created_by_id=person_id
        ).id
        for i in range(2)
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
    for i, (species_id, brain_region_id, morphology_id) in enumerate(
        it.product(species_ids, brain_region_ids, morphology_ids)
    ):
        emodel_id = assert_request(
            client.post,
            url="/emodel",
            json={
                "name": f"e-{i}",
                "brain_region_id": str(brain_region_id),
                "description": f"species{species_id}, brain_region{brain_region_id}, ex_morphology{morphology_id}",  # noqa: E501
                "species_id": str(species_id),
                "iteration": "test iteration",
                "score": 10 * i,
                "seed": -1,
                "exemplar_morphology_id": str(morphology_id),
                "authorized_public": False,
                "created_by_id": str(person_id),
                "updated_by_id": str(person_id),
            },
        ).json()["id"]

        emodel_ids.append(str(emodel_id))

    return EModelIds(
        emodel_ids=emodel_ids,
        species_ids=species_ids,
        brain_region_ids=brain_region_ids,
        morphology_ids=morphology_ids,
    )


@pytest.fixture
def faceted_memodels(db: Session, client: TestClient, agents: tuple[Agent, Agent, Role]):
    person_id = agents[1].id
    species_ids = [
        str(
            add_db(
                db,
                Species(
                    name=f"TestSpecies{i}",
                    taxonomy_id=f"{i}",
                    created_by_id=person_id,
                    updated_by_id=person_id,
                ),
            ).id
        )
        for i in range(2)
    ]

    strain_ids = [
        str(
            add_db(
                db,
                Strain(
                    name=f"TestStrain{i}",
                    taxonomy_id=f"{i + 2}",
                    species_id=species_ids[i],
                    created_by_id=person_id,
                    updated_by_id=person_id,
                ),
            ).id
        )
        for i in range(2)
    ]
    hierarchy_name = utils.create_hiearchy_name(db, "test_hier", created_by_id=person_id)
    brain_region_ids = [
        utils.create_brain_region(
            db, hierarchy_name.id, i, f"region{i}", created_by_id=person_id
        ).id
        for i in range(2)
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
                    created_by_id=person_id,
                    updated_by_id=person_id,
                ),
            ).id
        )
        for i in range(2)
    ]

    agent_ids = [str(agents[0].id), str(agents[1].id)]

    memodels = []

    for i, (species_id, brain_region_id, morphology_id, emodel_id) in enumerate(
        it.product(species_ids, brain_region_ids, morphology_ids, emodel_ids)
    ):
        memodel = add_db(
            db,
            MEModel(
                name=f"m-{i}",
                description="foo" if species_id == species_ids[0] else "bar",
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=None,
                morphology_id=morphology_id,
                emodel_id=emodel_id,
                authorized_public=False,
                authorized_project_id=PROJECT_ID,
                created_by_id=person_id,
                updated_by_id=person_id,
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


@pytest.fixture
def electrical_cell_recording_json_data(brain_region_id, subject_id, license_id):
    return {
        "name": "my-name",
        "description": "my-description",
        "subject_id": subject_id,
        "brain_region_id": str(brain_region_id),
        "license_id": str(license_id),
        "recording_location": ["soma[0]_0.5"],
        "recording_type": "intracellular",
        "recording_origin": "in_vivo",
        "ljp": 11.5,
        "authorized_public": False,
    }


@pytest.fixture
def trace_id_minimal(client, electrical_cell_recording_json_data):
    return utils.create_electrical_cell_recording_id(client, electrical_cell_recording_json_data)


@pytest.fixture
def trace_id_with_assets(db, client, tmp_path, electrical_cell_recording_json_data):
    return create_electrical_cell_recording_id_with_assets(
        db, client, tmp_path, electrical_cell_recording_json_data
    )


@pytest.fixture
def root_circuit_json_data(brain_atlas_id, subject_id, brain_region_id, license_id):
    return {
        "name": "root-circuit",
        "description": "root-circuit-description",
        "number_neurons": 10_000_000,
        "number_synapses": 1_000_000_000,
        "number_connections": 100_000_000,
        "has_morphologies": True,
        "has_point_neurons": True,
        "has_spines": True,
        "has_electrical_cell_models": True,
        "scale": "whole_brain",
        "root_circuit_id": None,
        "atlas_id": str(brain_atlas_id),
        "subject_id": str(subject_id),
        "build_category": "em_reconstruction",
        "authorized_project_id": PROJECT_ID,
        "authorized_public": False,
        "created_by_id": str(person_id),
        "updated_by_id": str(person_id),
        "brain_region_id": str(brain_region_id),
        "license_id": str(license_id),
    }


@pytest.fixture
def root_circuit(db, root_circuit_json_data, person_id):
    return add_db(
        db,
        Circuit(
            **root_circuit_json_data
            | {
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_project_id": PROJECT_ID,
            }
        ),
    )


@pytest.fixture
def circuit_json_data(brain_atlas_id, root_circuit, subject_id, brain_region_id, license_id):
    return {
        "name": "my-circuit",
        "description": "My Circuit",
        "has_morphologies": True,
        "has_point_neurons": False,
        "has_electrical_cell_models": True,
        "has_spines": False,
        "number_neurons": 5,
        "number_synapses": 100,
        "number_connections": 10,
        "scale": "microcircuit",
        "build_category": "computational_model",
        "atlas_id": str(brain_atlas_id),
        "root_circuit_id": str(root_circuit.id),
        "subject_id": str(subject_id),
        "brain_region_id": str(brain_region_id),
        "license_id": str(license_id),
        "authorized_public": False,
    }


@pytest.fixture
def circuit(db, circuit_json_data, person_id):
    return add_db(
        db,
        Circuit(
            **circuit_json_data
            | {
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_project_id": PROJECT_ID,
            }
        ),
    )


@pytest.fixture
def simulation_campaign_json_data(circuit):
    return {
        "name": "simulation-campaign",
        "description": "simulation-campaign-description",
        "scan_parameters": {"foo1": "bar2"},
        "entity_id": str(circuit.id),
    }


@pytest.fixture
def simulation_campaign(db, simulation_campaign_json_data, person_id):
    return add_db(
        db,
        SimulationCampaign(
            **simulation_campaign_json_data
            | {
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_project_id": PROJECT_ID,
            }
        ),
    )


@pytest.fixture
def simulation_json_data(simulation_campaign, circuit):
    return {
        "name": "simulation",
        "description": "simulation-description",
        "entity_id": str(circuit.id),
        "simulation_campaign_id": str(simulation_campaign.id),
        "scan_parameters": {"foo1": "bar1", "foo2": "bar2"},
    }


@pytest.fixture
def simulation(db, simulation_json_data, person_id):
    return add_db(
        db,
        Simulation(
            **simulation_json_data
            | {
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_project_id": PROJECT_ID,
            }
        ),
    )


@pytest.fixture
def simulation_result_json_data(simulation):
    return {
        "name": "simulation-result",
        "description": "simulation-result-description",
        "simulation_id": str(simulation.id),
    }


@pytest.fixture
def simulation_result(db, simulation_result_json_data, person_id):
    return add_db(
        db,
        SimulationResult(
            **simulation_result_json_data
            | {
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_project_id": PROJECT_ID,
            },
        ),
    )


@pytest.fixture
def publication_json_data():
    return {
        "name": "my-publication",
        "description": "my-publication",
        "DOI": "my-doi",
        "title": "my-title",
        "authors": [
            {
                "given_name": "John",
                "family_name": "Smith",
            },
            {
                "given_name": "Joanne",
                "family_name": "Smith",
            },
        ],
        "publication_year": 2024,
        "abstract": "my-abstract",
    }


@pytest.fixture
def publication(db, publication_json_data, person_id):
    return add_db(
        db,
        Publication(
            **publication_json_data
            | {
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_project_id": PROJECT_ID,
            }
        ),
    )
