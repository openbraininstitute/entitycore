import itertools as it

import pytest

from app.db.model import MEModel, SingleNeuronSimulation

from .utils import (
    BEARER_TOKEN,
    MISSING_ID,
    MISSING_ID_COMPACT,
    PROJECT_HEADERS,
    PROJECT_ID,
    add_db,
    assert_request,
)

ROUTE = "/single-neuron-simulation"


@pytest.mark.usefixtures("skip_project_check")
def test_single_neuron_simulation(client, brain_region_id, memodel_id):
    response = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "name": "foo",
            "description": "my-description",
            "injectionLocation": ["soma[0]"],
            "recordingLocation": ["soma[0]_0.5"],
            "me_model_id": memodel_id,
            "status": "success",
            "seed": 1,
            "authorized_public": False,
            "brain_region_id": str(brain_region_id),
        },
    )

    data = response.json()
    assert data["brain_region"]["id"] == brain_region_id, (
        f"Failed to get id for reconstruction morphology: {data}"
    )
    assert data["description"] == "my-description"
    assert data["name"] == "foo"
    assert data["injectionLocation"] == ["soma[0]"]
    assert data["recordingLocation"] == ["soma[0]_0.5"]
    assert data["me_model"]["id"] == memodel_id, f"Failed to get id frmo me model; {data}"
    assert data["status"] == "success"
    assert data["authorized_project_id"] == PROJECT_HEADERS["project-id"]

    response = assert_request(
        client.get,
        url=f"{ROUTE}/{data['id']}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert data["brain_region"]["id"] == brain_region_id, (
        f"Failed to get id for reconstruction morphology: {data}"
    )
    assert data["description"] == "my-description"
    assert data["name"] == "foo"
    assert data["injectionLocation"] == ["soma[0]"]
    assert data["recordingLocation"] == ["soma[0]_0.5"]
    assert data["me_model"]["id"] == memodel_id, f"Failed to get id frmo me model; {data}"
    assert data["status"] == "success"
    assert data["authorized_project_id"] == PROJECT_HEADERS["project-id"]


@pytest.mark.usefixtures("skip_project_check")
@pytest.mark.parametrize(
    ("route_id", "expected_status_code"),
    [
        (MISSING_ID, 404),
        (MISSING_ID_COMPACT, 404),
        ("42424242", 422),
        ("notanumber", 422),
    ],
)
def test_missing(client, route_id, expected_status_code):
    assert_request(
        client.get,
        url=f"{ROUTE}/{route_id}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        expected_status_code=expected_status_code,
    )


@pytest.mark.usefixtures("skip_project_check")
def test_authorization(client, memodel_id, brain_region_id):
    json_data = {
        "name": "foo",
        "description": "my-description",
        "injectionLocation": ["soma[0]"],
        "recordingLocation": ["soma[0]_0.5"],
        "me_model_id": memodel_id,
        "status": "failure",
        "seed": 1,
        "brain_region_id": str(brain_region_id),
    }

    response = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=json_data
        | {
            "name": "Public Entity",
            "authorized_public": True,
        },
    )
    public_morph = response.json()

    inaccessible_obj = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN
        | {
            "virtual-lab-id": "42424242-4242-4000-9000-424242424242",
            "project-id": "42424242-4242-4000-9000-424242424242",
        },
        json=json_data | {"name": "unaccessable morphology 1"},
    )
    inaccessible_obj = inaccessible_obj.json()

    private_obj0 = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=json_data | {"name": "private morphology 0"},
    )
    private_obj0 = private_obj0.json()

    private_obj1 = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=json_data
        | {
            "name": "private morphology 1",
        },
    )
    private_obj1 = private_obj1.json()

    # only return results that matches the desired project, and public ones
    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    data = response.json()["data"]

    ids = {row["id"] for row in data}
    assert ids == {
        public_morph["id"],
        private_obj0["id"],
        private_obj1["id"],
    }, data

    assert_request(
        client.get,
        url=f"{ROUTE}/{inaccessible_obj['id']}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        expected_status_code=404,
    )


@pytest.mark.usefixtures("skip_project_check")
def test_pagination(db, client, brain_region_id, emodel_id, morphology_id, species_id):
    me_model_1 = add_db(
        db,
        MEModel(
            name="me-model-1",
            description="my-description-1",
            brain_region_id=brain_region_id,
            authorized_project_id=PROJECT_ID,
            emodel_id=emodel_id,
            mmodel_id=morphology_id,
            species_id=species_id,
        ),
    )
    me_model_2 = add_db(
        db,
        MEModel(
            name="my-me-model",
            description="my-description",
            brain_region_id=brain_region_id,
            authorized_project_id=PROJECT_ID,
            emodel_id=emodel_id,
            mmodel_id=morphology_id,
            species_id=species_id,
        ),
    )

    def create(count):
        ids = []
        for i, me_model in zip(range(count), it.cycle((me_model_1, me_model_2))):
            row = SingleNeuronSimulation(
                name=f"sim-{i}",
                description="my-description",
                injectionLocation=["soma[0]"],
                recordingLocation=["soma[0]_0.5"],
                me_model_id=me_model.id,
                status="success",
                seed=1,
                authorized_public=False,
                brain_region_id=brain_region_id,
                authorized_project_id=PROJECT_ID,
            )
            add_db(db, row)
            ids.append(row.id)

    count = 7
    create(count)

    response = assert_request(
        client.get,
        url=ROUTE,
        params={"page_size": 3},
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 3
