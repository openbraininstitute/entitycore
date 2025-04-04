import itertools as it

import pytest

from app.db.model import SingleNeuronSynaptome, SingleNeuronSynaptomeSimulation

from .utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    PROJECT_ID,
    add_db,
    assert_request,
    create_brain_region_id,
)

ROUTE = "/single-neuron-synaptome-simulation"


def _create_synaptome_id(
    db,
    *,
    memodel_id,
    brain_region_id,
    name="my-synaptome",
    description="my-synaptome-description",
    seed=1,
    authorized_public=False,
    authorized_project_id=PROJECT_ID,
):
    return add_db(
        db,
        SingleNeuronSynaptome(
            name=name,
            description=description,
            me_model_id=str(memodel_id),
            brain_region_id=brain_region_id,
            seed=seed,
            authorized_public=authorized_public,
            authorized_project_id=authorized_project_id,
        ),
    ).id


@pytest.fixture
def synaptome_id(db, memodel_id, brain_region_id):
    return _create_synaptome_id(
        db,
        memodel_id=memodel_id,
        brain_region_id=brain_region_id,
    )


@pytest.fixture
def json_data(brain_region_id, synaptome_id):
    return {
        "name": "my-sim",
        "description": "my-description",
        "injectionLocation": ["soma[0]"],
        "recordingLocation": ["soma[0]_0.5"],
        "status": "success",
        "seed": 1,
        "synaptome_id": str(synaptome_id),
        "brain_region_id": brain_region_id,
        "authorized_public": False,
    }


def _create_simulation_id(
    db,
    *,
    synaptome_id,
    brain_region_id,
    name="my-synaptome-simulation",
    description="my-synaptome-simulation-description",
    injectionLocation=None,  # noqa: N803
    recordingLocation=None,  # noqa: N803
    status="success",
    seed=1,
    authorized_public=False,
    authorized_project_id=PROJECT_ID,
):
    if injectionLocation is None:
        injectionLocation = ["soma[0]"]  # noqa: N806

    if recordingLocation is None:
        recordingLocation = ["soma[0]_0.5"]  # noqa: N806

    return add_db(
        db,
        SingleNeuronSynaptomeSimulation(
            name=name,
            description=description,
            injectionLocation=injectionLocation,
            recordingLocation=recordingLocation,
            status=status,
            seed=seed,
            synaptome_id=str(synaptome_id),
            brain_region_id=brain_region_id,
            authorized_public=authorized_public,
            authorized_project_id=authorized_project_id,
        ),
    ).id


@pytest.fixture
def simulation_id(db, json_data):
    data = json_data | {"authorized_project_id": PROJECT_ID}
    return _create_simulation_id(db, **data)


def test_create_one(client, json_data, brain_region_id, synaptome_id):
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data,
    ).json()
    assert data["brain_region"]["id"] == brain_region_id
    assert data["description"] == "my-description"
    assert data["name"] == "my-sim"
    assert data["status"] == "success"
    assert data["injectionLocation"] == ["soma[0]"]
    assert data["recordingLocation"] == ["soma[0]_0.5"]
    assert data["synaptome"]["id"] == str(synaptome_id)
    assert data["authorized_project_id"] == PROJECT_ID


def test_read_one(client, brain_region_id, synaptome_id, simulation_id):
    data = assert_request(
        client.get,
        url=f"{ROUTE}/{simulation_id}",
    ).json()
    assert data["brain_region"]["id"] == brain_region_id
    assert data["description"] == "my-description"
    assert data["name"] == "my-sim"
    assert data["status"] == "success"
    assert data["injectionLocation"] == ["soma[0]"]
    assert data["recordingLocation"] == ["soma[0]_0.5"]
    assert data["synaptome"]["id"] == str(synaptome_id)
    assert data["authorized_project_id"] == PROJECT_ID


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
        expected_status_code=expected_status_code,
    )


def test_authorization(client_user_1, client_user_2, client_no_project, json_data):
    response = assert_request(
        client_user_1.post,
        url=ROUTE,
        json=json_data
        | {
            "name": "Public Entity",
            "authorized_public": True,
        },
    )
    public_morph = response.json()

    inaccessible_obj = assert_request(
        client_user_2.post,
        url=ROUTE,
        json=json_data | {"name": "inaccessable morphology 1"},
    )
    inaccessible_obj = inaccessible_obj.json()

    private_obj0 = assert_request(
        client_user_1.post,
        url=ROUTE,
        json=json_data | {"name": "private morphology 0"},
    )
    private_obj0 = private_obj0.json()

    private_obj1 = assert_request(
        client_user_1.post,
        url=ROUTE,
        json=json_data
        | {
            "name": "private morphology 1",
        },
    )
    private_obj1 = private_obj1.json()

    # only return results that matches the desired project, and public ones
    response = assert_request(
        client_user_1.get,
        url=ROUTE,
    )
    data = response.json()["data"]

    ids = {row["id"] for row in data}
    assert ids == {
        public_morph["id"],
        private_obj0["id"],
        private_obj1["id"],
    }, data

    assert_request(
        client_user_1.get,
        url=f"{ROUTE}/{inaccessible_obj['id']}",
        expected_status_code=404,
    )

    # only returns public results
    response = assert_request(
        client_no_project.get,
        url=ROUTE,
    )
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == public_morph["id"]


def test_pagination(db, client, brain_region_id, memodel_id):
    synaptome_1_id = _create_synaptome_id(
        db, name="syn-1", memodel_id=memodel_id, brain_region_id=brain_region_id
    )
    synaptome_2_id = _create_synaptome_id(
        db,
        name="syn-2",
        memodel_id=memodel_id,
        brain_region_id=brain_region_id,
    )

    def create(count):
        ids = []
        for i, synaptome_id in zip(range(count), it.cycle((synaptome_1_id, synaptome_2_id))):
            sim_id = _create_simulation_id(
                db,
                name=f"sim-{i}",
                synaptome_id=synaptome_id,
                brain_region_id=brain_region_id,
            )
            ids.append(sim_id)

    count = 7
    create(count)

    response = assert_request(
        client.get,
        url=ROUTE,
        params={"page_size": 3},
    )
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 3


@pytest.fixture
def faceted_ids(db, client_admin, memodel_id):
    brain_region_ids = [
        create_brain_region_id(client_admin, id_=i, name=f"region-{i}") for i in range(2)
    ]
    synaptome_ids = [
        _create_synaptome_id(
            db,
            name=f"synaptome-{i}",
            description=f"description-{i}",
            brain_region_id=brain_region_ids[i],
            memodel_id=memodel_id,
        )
        for i in range(2)
    ]
    single_simulation_synaptome_ids = [
        _create_simulation_id(
            db,
            name=f"synaptome-{i}",
            description=f"brain-region-{brain_region_id} synaptome-{synaptome_id}",
            seed=i,
            synaptome_id=synaptome_id,
            brain_region_id=brain_region_id,
        )
        for i, (synaptome_id, brain_region_id) in enumerate(
            it.product(synaptome_ids, brain_region_ids)
        )
    ]
    return brain_region_ids, synaptome_ids, single_simulation_synaptome_ids


def test_facets(client, faceted_ids):
    brain_region_ids, synaptome_ids, _ = faceted_ids

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"with_facets": True},
    ).json()

    assert "facets" in data
    facets = data["facets"]

    assert facets["contribution"] == []
    assert facets["brain_region"] == [
        {"id": brain_region_ids[0], "label": "region-0", "count": 2, "type": "brain_region"},
        {"id": brain_region_ids[1], "label": "region-1", "count": 2, "type": "brain_region"},
    ]
    assert facets["single_neuron_synaptome"] == [
        {
            "id": str(synaptome_ids[0]),
            "label": "synaptome-0",
            "count": 2,
            "type": "single_neuron_synaptome",
        },
        {
            "id": str(synaptome_ids[1]),
            "label": "synaptome-1",
            "count": 2,
            "type": "single_neuron_synaptome",
        },
    ]

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"search": f"synaptome-{synaptome_ids[0]}", "with_facets": True},
    ).json()

    assert "facets" in data
    facets = data["facets"]

    assert facets["single_neuron_synaptome"] == [
        {
            "id": str(synaptome_ids[0]),
            "label": "synaptome-0",
            "count": 2,
            "type": "single_neuron_synaptome",
        }
    ]

    assert facets["brain_region"] == [
        {"id": 0, "label": "region-0", "count": 1, "type": "brain_region"},
        {"id": 1, "label": "region-1", "count": 1, "type": "brain_region"},
    ]
