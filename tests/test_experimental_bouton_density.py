import pytest

from app.db.model import ExperimentalBoutonDensity
from app.db.types import EntityType
from app.schemas.density import ExperimentalBoutonDensityCreate

from .utils import (
    PROJECT_ID,
    assert_request,
    check_authorization,
    check_brain_region_filter,
    check_missing,
    check_pagination,
)

ROUTE = "/experimental-bouton-density"


@pytest.fixture
def json_data(brain_region_id, subject_id, license_id):
    return ExperimentalBoutonDensityCreate(
        name="my-name",
        description="my-description",
        brain_region_id=brain_region_id,
        subject_id=subject_id,
        legacy_id="Test Legacy ID",
        license_id=license_id,
    ).model_dump(mode="json")


def _assert_read_response(data, json_data):
    assert data["brain_region"]["id"] == json_data["brain_region_id"]
    assert data["subject"]["id"] == json_data["subject_id"]
    assert data["description"] == json_data["description"]
    assert data["name"] == json_data["name"]
    assert data["license"]["name"] == "Test License"
    assert data["type"] == EntityType.experimental_bouton_density


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


@pytest.fixture
def model_id(create_id):
    return create_id()


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_read_one(client, model_id, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model_id}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=ROUTE).json()
    assert len(data["data"]) == 1


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(
    client_user_1,
    client_user_2,
    client_no_project,
    json_data,
):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


def test_brain_region_filter(db, client, brain_region_hierarchy_id, subject_id):
    def create_model_function(_db, name, brain_region_id):
        return ExperimentalBoutonDensity(
            name=name,
            description="my-description",
            brain_region_id=brain_region_id,
            subject_id=subject_id,
            license_id=None,
            authorized_project_id=PROJECT_ID,
        )

    check_brain_region_filter(ROUTE, client, db, brain_region_hierarchy_id, create_model_function)
