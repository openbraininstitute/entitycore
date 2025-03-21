import itertools as it

import pytest

from app.db.model import MEModel, SingleNeuronSynaptome

from .utils import (
    BEARER_TOKEN,
    MISSING_ID,
    MISSING_ID_COMPACT,
    PROJECT_HEADERS,
    PROJECT_ID,
    add_db,
    assert_request,
    create_brain_region_id,
)

ROUTE = "/single-neuron-synaptome"


def _create_me_model_id(db, data):
    return add_db(db, MEModel(**data)).id


@pytest.fixture
def me_model_id(db, brain_region_id):
    return _create_me_model_id(
        db,
        {
            "name": "my-me-model",
            "description": "my-description",
            "validated": False,
            "brain_region_id": brain_region_id,
            "authorized_project_id": PROJECT_ID,
        },
    )


@pytest.fixture
def json_data(brain_region_id, me_model_id):
    return {
        "name": "my-synaptome",
        "description": "my-description",
        "me_model_id": str(me_model_id),
        "seed": 1,
        "brain_region_id": str(brain_region_id),
    }


def _create_single_neuron_synaptome_id(db, data):
    return add_db(db, SingleNeuronSynaptome(**data)).id


@pytest.fixture
def single_neuron_synaptome_id(db, json_data):
    data = json_data | {"authorized_project_id": PROJECT_ID}
    return _create_single_neuron_synaptome_id(db, data)


@pytest.mark.usefixtures("skip_project_check")
def test_create_one(client, brain_region_id, me_model_id, json_data):
    data = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=json_data,
    ).json()

    assert data["brain_region"]["id"] == brain_region_id, (
        f"Failed to get id for reconstruction morphology: {data}"
    )
    assert data["description"] == "my-description"
    assert data["name"] == "my-synaptome"
    assert data["me_model"]["id"] == str(me_model_id), f"Failed to get id frmo me model; {data}"
    assert data["authorized_project_id"] == PROJECT_HEADERS["project-id"]


@pytest.mark.usefixtures("skip_project_check")
def test_read_one(client, brain_region_id, single_neuron_synaptome_id, me_model_id):
    data = assert_request(
        client.get,
        url=f"{ROUTE}/{single_neuron_synaptome_id}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    ).json()
    assert data["brain_region"]["id"] == brain_region_id, (
        f"Failed to get id for reconstruction morphology: {data}"
    )
    assert data["description"] == "my-description"
    assert data["name"] == "my-synaptome"
    assert data["me_model"]["id"] == str(me_model_id), f"Failed to get id frmo me model; {data}"
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
def test_authorization(client, json_data):
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
            row = SingleNeuronSynaptome(
                name=f"sim-{i}",
                description="my-description",
                me_model_id=me_model.id,
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


@pytest.fixture
def faceted_ids(db, client):
    brain_region_ids = [create_brain_region_id(client, id_=i, name=f"region-{i}") for i in range(2)]
    me_model_ids = [
        _create_me_model_id(
            db,
            {
                "name": f"me-model-{i}",
                "description": f"description-{i}",
                "validated": False,
                "brain_region_id": brain_region_ids[i],
                "authorized_project_id": PROJECT_ID,
            },
        )
        for i in range(2)
    ]
    single_simulation_synaptome_ids = [
        _create_single_neuron_synaptome_id(
            db,
            {
                "name": f"synaptome-{i}",
                "description": f"brain-region-{brain_region_id} me-model-{me_model_id}",
                "me_model_id": str(me_model_id),
                "seed": i,
                "brain_region_id": str(brain_region_id),
                "authorized_project_id": PROJECT_ID,
            },
        )
        for i, (me_model_id, brain_region_id) in enumerate(
            it.product(me_model_ids, brain_region_ids)
        )
    ]
    return brain_region_ids, me_model_ids, single_simulation_synaptome_ids


@pytest.mark.usefixtures("skip_project_check")
def test_facets(client, faceted_ids):
    brain_region_ids, me_model_ids, _ = faceted_ids

    data = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"with_facets": True},
    ).json()

    assert "facets" in data
    facets = data["facets"]

    assert facets["contribution"] == []
    assert facets["brain_region"] == [
        {"id": brain_region_ids[0], "label": "region-0", "count": 2, "type": "brain_region"},
        {"id": brain_region_ids[1], "label": "region-1", "count": 2, "type": "brain_region"},
    ]
    assert facets["me_model"] == [
        {
            "id": str(me_model_ids[0]),
            "label": "me-model-0",
            "count": 2,
            "type": "me_model",
        },
        {
            "id": str(me_model_ids[1]),
            "label": "me-model-1",
            "count": 2,
            "type": "me_model",
        },
    ]

    data = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"search": f"me-model-{me_model_ids[0]}", "with_facets": True},
    ).json()

    assert "facets" in data
    facets = data["facets"]

    assert facets["me_model"] == [
        {
            "id": str(me_model_ids[0]),
            "label": "me-model-0",
            "count": 2,
            "type": "me_model",
        }
    ]

    assert facets["brain_region"] == [
        {"id": 0, "label": "region-0", "count": 1, "type": "brain_region"},
        {"id": 1, "label": "region-1", "count": 1, "type": "brain_region"},
    ]
