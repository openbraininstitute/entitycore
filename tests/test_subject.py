from datetime import timedelta

import pytest

from app.db.model import Subject
from app.schemas.subject import SubjectCreate

from .utils import (
    PROJECT_ID,
    add_all_db,
    assert_request,
    check_authorization,
    check_missing,
    check_pagination,
)

ROUTE = "/subject"
MODEL_CLASS = Subject


@pytest.fixture
def json_data(species_id):
    return SubjectCreate(
        sex="female",
        name="my-subject",
        description="my-description",
        species_id=species_id,
        age_value=timedelta(days=14),
        age_period="postnatal",
    ).model_dump(mode="json")


def _assert_read_response(data, json_data):
    assert data["description"] == json_data["description"]
    assert data["name"] == json_data["name"]
    assert data["species"]["id"] == json_data["species_id"]
    assert data["authorized_project_id"] == PROJECT_ID
    assert data["age_value"] == 14.0 * 24.0 * 3600.0
    assert data["age_min"] is None
    assert data["age_max"] is None
    assert data["age_period"] == "postnatal"


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


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, json_data):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


def test_schema_constraints(client, json_data):
    # remove keys we want to test for schema validation
    for key in ("age_value", "age_min", "age_max", "age_period"):
        json_data.pop(key, None)

    # check age_period is needed when an age is set
    for key in ("age_value", "age_min", "age_max"):
        assert_request(
            client.post, url=ROUTE, json=json_data | {key: 1.0}, expected_status_code=422
        )

    # put it back now that we checked it
    json_data["age_period"] = "postnatal"

    # check constraint value > 0.0
    for key in ("age_value", "age_min", "age_max", "weight"):
        assert_request(
            client.post, url=ROUTE, json=json_data | {key: 0.0}, expected_status_code=422
        )
    # age_value and minmax range cannot be specified together
    assert_request(
        client.post,
        url=ROUTE,
        json=json_data | {"age_value": 1.0, "age_min": 1.0, "age_max": 2.0},
        expected_status_code=422,
    )
    # age min and max must specified together
    assert_request(
        client.post, url=ROUTE, json=json_data | {"age_min": 1.0}, expected_status_code=422
    )
    # age min > max
    assert_request(
        client.post,
        url=ROUTE,
        json=json_data | {"age_min": 2.0, "age_max": 1.0},
        expected_status_code=422,
    )
    assert_request(
        client.post,
        url=ROUTE,
        json=json_data | {"age_min": 1.0, "age_max": 1.0},
        expected_status_code=422,
    )


@pytest.fixture
def models(db, person_id, species_id):
    rows = [
        Subject(
            sex="female",
            name=f"my-subject-{i}",
            description="my-description-{i}",
            species_id=species_id,
            age_value=timedelta(days=i + 1),
            age_period="postnatal",
            created_by_id=person_id,
            updated_by_id=person_id,
            authorized_project_id=PROJECT_ID,
            creation_date=f"2025-01-01 00:00:{i:02}",
        )
        for i in range(5)
    ]
    return add_all_db(db, rows)


def test_filtering_sorting(client, models):
    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    data = req({})
    assert len(data) == len(models)

    data = req({"name": "my-subject-1"})
    assert len(data) == 1

    data = req({"name": "my-subject"})
    assert len(data) == 0

    data = req({"age_value": "2 days"})
    assert len(data) == 1

    data = req({"age_value": "99 days"})
    assert len(data) == 0

    data = req({"name__in": ["my-subject-1", "my-subject-2"], "order_by": "creation_date"})
    assert [d["name"] for d in data] == ["my-subject-1", "my-subject-2"]

    data = req({"name__in": ["my-subject-1", "my-subject-2"], "order_by": "-creation_date"})
    assert [d["name"] for d in data] == ["my-subject-2", "my-subject-1"]
