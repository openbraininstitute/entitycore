from functools import partial

import pytest

from app.db.model import ExperimentalNeuronDensity

from .utils import (
    PROJECT_ID,
    add_db,
    assert_request,
    check_authorization,
    check_missing,
    check_pagination,
)

ROUTE = "/experimental-neuron-density"
MODEL_CLASS = ExperimentalNeuronDensity


@pytest.fixture
def json_data(brain_region_id, species_id, strain_id, license_id):
    return {
        "brain_region_id": brain_region_id,
        "species_id": species_id,
        "strain_id": strain_id,
        "description": "my-description",
        "name": "my-name",
        "legacy_id": "Test Legacy ID",
        "license_id": license_id,
    }


@pytest.fixture
def model_id(db, json_data):
    return create_id(db=db, **json_data)


def create_id(
    db,
    species_id,
    strain_id,
    brain_region_id,
    license_id,
    name="my-density",
    description="my-description",
    legacy_id="my-legacy-id",
    authorized_public=False,  # noqa: FBT002
    authorized_project_id=PROJECT_ID,
):
    return str(
        add_db(
            db,
            MODEL_CLASS(
                name=name,
                description=description,
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=strain_id,
                license_id=license_id,
                authorized_public=authorized_public,
                authorized_project_id=authorized_project_id,
                legacy_id=legacy_id,
            ),
        ).id
    )


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    assert data["brain_region"]["id"] == json_data["brain_region_id"]
    assert data["species"]["id"] == json_data["species_id"]
    assert data["strain"]["id"] == json_data["strain_id"]
    assert data["description"] == json_data["description"]
    assert data["name"] == json_data["name"]
    assert data["license"]["name"] == "Test License"


def test_read_one(client, model_id, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model_id}").json()
    assert data["brain_region"]["id"] == json_data["brain_region_id"]
    assert data["species"]["id"] == json_data["species_id"]
    assert data["strain"]["id"] == json_data["strain_id"]
    assert data["description"] == json_data["description"]

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


def test_pagination(client, db, species_id, strain_id, license_id, brain_region_id):
    constructor_func = partial(
        create_id,
        db=db,
        species_id=species_id,
        strain_id=strain_id,
        license_id=license_id,
        brain_region_id=brain_region_id,
    )
    check_pagination(ROUTE, client, constructor_func)
