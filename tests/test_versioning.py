import pytest
import sqlalchemy as sa

from app.db.model import CellMorphology
from app.db.types import ResourceType
from app.schemas.cell_morphology import CellMorphologyRead
from app.service.versioning import RESOURCE_TYPE_TO_READ_SCHEMA
from app.utils.routers import NOT_ROUTABLE_RESOURCES

from .utils import add_contribution, assert_request

ROUTE = "/cell-morphology"


@pytest.fixture
def json_data(subject_id, license_id, brain_region_id, cell_morphology_protocol):
    return {
        "brain_region_id": str(brain_region_id),
        "subject_id": str(subject_id),
        "description": "Test Morphology Description",
        "name": "Test Morphology Name",
        "location": {"x": 10, "y": 20, "z": 30},
        "legacy_id": ["Test Legacy ID"],
        "license_id": str(license_id),
        "cell_morphology_protocol_id": str(cell_morphology_protocol.id),
        "contact_email": "test@example.com",
        "notice_text": "Notice text example",
        "experiment_date": "2025-01-01T00:00:00",
        "repair_pipeline_state": "raw",
    }


def test_routes_are_complete():
    expected = {str(t) for t in ResourceType if t not in NOT_ROUTABLE_RESOURCES}
    assert set(RESOURCE_TYPE_TO_READ_SCHEMA) == expected


def test_read_version_from_db(db, client, json_data, person_id, role_id):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    entity_id = data["id"]

    add_contribution(
        db,
        entity_id=entity_id,
        agent_id=person_id,
        role_id=role_id,
        created_by_id=person_id,
    )

    query = sa.select(CellMorphology).where(CellMorphology.id == entity_id)
    entity = db.execute(query).scalar_one()

    # get the first version
    version = entity.versions[0]
    for k in sorted(dir(version)):
        if k.startswith("_"):
            continue
        if k in {
            "metadata",
            "transaction",
            "operation_type",
            "version_parent",
            "changeset",
            "previous",
            "next",
            "generated_entities",  # exclude viewonly many-to-many associations, not supported
            "usage_activities",  # exclude viewonly many-to-many associations, not supported
        }:
            continue
        # get the attribute to trigger the related queries
        getattr(version, k)

    read = CellMorphologyRead.model_validate(version)
    assert str(read.id) == entity_id


def test_read_version_from_api(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    entity_id = data["id"]

    data = assert_request(client.get, url=f"{ROUTE}/{entity_id}/version-count").json()
    assert data == 1

    data = assert_request(client.get, url=f"{ROUTE}/{entity_id}/version/0").json()
    assert data["id"] == entity_id

    data = assert_request(client.get, url=f"{ROUTE}/{entity_id}/version/0/changeset").json()
    assert isinstance(data, dict)
    assert data["id"] == [None, entity_id]
