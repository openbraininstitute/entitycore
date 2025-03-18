import itertools as it

import pytest

from app.db.model import MEModel, SingleNeuronSimulation

from .utils import BEARER_TOKEN, PROJECT_HEADERS, add_db, MISSING_ID, MISSING_ID_COMPACT

ROUTE = "/single-neuron-simulation"


@pytest.mark.usefixtures("skip_project_check")
def test_single_neuron_simulation(client, db, brain_region_id):
    row = MEModel(
        name="my-me-model",
        description="my-description",
        status="foo",
        validated=False,
        brain_region_id=brain_region_id,
        authorized_project_id=PROJECT_HEADERS["project-id"],
    )
    add_db(db, row)

    me_model_id = row.id

    response = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "name": "foo",
            "description": "my-description",
            "injectionLocation": ["soma[0]"],
            "recordingLocation": ["soma[0]_0.5"],
            "me_model_id": me_model_id,
            "status": "foo",
            "seed": 1,
            "authorized_public": False,
            "brain_region_id": brain_region_id,
        },
    )
    assert response.status_code == 200, response.content

    data = response.json()
    assert data["brain_region"]["id"] == brain_region_id, (
        f"Failed to get id for reconstruction morphology: {data}"
    )
    assert data["description"] == "my-description"
    assert data["name"] == "foo"
    assert data["injectionLocation"] == ["soma[0]"]
    assert data["recordingLocation"] == ["soma[0]_0.5"]
    assert data["me_model"]["id"] == me_model_id, f"Failed to get id frmo me model; {data}"
    assert data["status"] == "foo"
    assert data["authorized_project_id"] == PROJECT_HEADERS["project-id"]

    response = client.get(f"{ROUTE}/{data['id']}", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 200, response.content
    assert data["brain_region"]["id"] == brain_region_id, (
        f"Failed to get id for reconstruction morphology: {data}"
    )
    assert data["description"] == "my-description"
    assert data["name"] == "foo"
    assert data["injectionLocation"] == ["soma[0]"]
    assert data["recordingLocation"] == ["soma[0]_0.5"]
    assert data["me_model"]["id"] == me_model_id, f"Failed to get id frmo me model; {data}"
    assert data["status"] == "foo"
    assert data["authorized_project_id"] == PROJECT_HEADERS["project-id"]


@pytest.mark.usefixtures("skip_project_check")
@pytest.mark.parametrize("route_id, expected_status_code", [
    (MISSING_ID, 404),
    (MISSING_ID_COMPACT, 404),
    ("42424242", 422),
    ("notanumber", 422),
])
def test_missing(client, route_id, expected_status_code):
    response = client.get(f"{ROUTE}/{route_id}", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == expected_status_code


@pytest.mark.usefixtures("skip_project_check")
def test_query(db, client, brain_region_id):
    me_model_1 = add_db(
        db,
        MEModel(
            name="me-model-1",
            description="my-description-1",
            status="Done",
            validated=False,
            brain_region_id=brain_region_id,
            authorized_project_id=PROJECT_HEADERS["project-id"],
        ),
    )
    me_model_2 = add_db(
        db,
        MEModel(
            name="my-me-model",
            description="my-description",
            status="foo",
            validated=False,
            brain_region_id=brain_region_id,
            authorized_project_id=PROJECT_HEADERS["project-id"],
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
                    status="foo",
                    seed=1,
                    authorized_public=False,
                    brain_region_id=brain_region_id,
                )
            add_db(db, row)
            ids.append(row.id)

    count = 7
    create(count)

    response = client.get(
        ROUTE,
        params={"page_size": 3},
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )

    assert response.status_code == 200
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 3
