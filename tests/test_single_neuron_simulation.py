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
    assert_authorization,
    assert_dict_equal,
    assert_request,
)

ROUTE = "/single-neuron-simulation"


@pytest.fixture
def me_model_id(db, brain_region_id):
    row = MEModel(
        name="my-me-model",
        description="my-description",
        status="started",
        validated=False,
        brain_region_id=brain_region_id,
        authorized_project_id=PROJECT_ID,
    )
    add_db(db, row)
    return row.id


@pytest.mark.usefixtures("skip_project_check")
def test_single_neuron_simulation(client, brain_region_id, me_model_id):
    response = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "name": "foo",
            "description": "my-description",
            "injectionLocation": ["soma[0]"],
            "recordingLocation": ["soma[0]_0.5"],
            "me_model_id": str(me_model_id),
            "status": "success",
            "seed": 1,
            "authorized_public": False,
            "brain_region_id": str(brain_region_id),
        },
    )
    data = response.json()
    assert_dict_equal(
        data,
        {
            "name": "foo",
            "description": "my-description",
            "brain_region.id": brain_region_id,
            "injectionLocation": ["soma[0]"],
            "recordingLocation": ["soma[0]_0.5"],
            "me_model.id": str(me_model_id),
            "status": "success",
            "authorized_project_id": PROJECT_ID,
        },
    )
    response = assert_request(
        client.get,
        url=f"{ROUTE}/{data['id']}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert_dict_equal(
        response.json(),
        {
            "name": "foo",
            "description": "my-description",
            "brain_region.id": brain_region_id,
            "injectionLocation": ["soma[0]"],
            "recordingLocation": ["soma[0]_0.5"],
            "me_model.id": str(me_model_id),
            "status": "success",
            "authorized_project_id": PROJECT_ID,
        },
    )


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
def test_authorization(client, me_model_id, brain_region_id):
    json_data = {
        "name": "foo",
        "description": "my-description",
        "injectionLocation": ["soma[0]"],
        "recordingLocation": ["soma[0]_0.5"],
        "me_model_id": str(me_model_id),
        "status": "failure",
        "seed": 1,
        "brain_region_id": str(brain_region_id),
    }
    assert_authorization(client=client, route=ROUTE, json_data=json_data)


@pytest.mark.usefixtures("skip_project_check")
def test_pagination(db, client, brain_region_id):
    me_model_1 = add_db(
        db,
        MEModel(
            name="me-model-1",
            description="my-description-1",
            status="foo",
            validated=False,
            brain_region_id=brain_region_id,
            authorized_project_id=PROJECT_ID,
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
            authorized_project_id=PROJECT_ID,
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
