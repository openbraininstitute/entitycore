import itertools as it

import pytest

from app.db.model import MEModel, SingleNeuronSynaptome

from .utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    PROJECT_ID,
    add_db,
    assert_request,
    create_brain_region,
)
from tests.conftest import CreateIds

ROUTE = "/single-neuron-synaptome"


@pytest.fixture
def json_data(brain_region_id, memodel_id):
    return {
        "name": "my-synaptome",
        "description": "my-description",
        "me_model_id": str(memodel_id),
        "seed": 1,
        "brain_region_id": str(brain_region_id),
    }


def _create_single_neuron_synaptome_id(db, data):
    return add_db(db, SingleNeuronSynaptome(**data)).id


@pytest.fixture
def single_neuron_synaptome_id(db, json_data):
    data = json_data | {"authorized_project_id": PROJECT_ID}
    return _create_single_neuron_synaptome_id(db, data)


def test_create_one(client, brain_region_id, memodel_id, json_data):
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data,
    ).json()

    assert data["brain_region"]["id"] == str(brain_region_id), (
        f"Failed to get id for reconstruction morphology: {data}"
    )
    assert data["description"] == "my-description"
    assert data["name"] == "my-synaptome"
    assert data["me_model"]["id"] == str(memodel_id), f"Failed to get id frmo me model; {data}"
    assert data["authorized_project_id"] == PROJECT_ID


def test_read_one(client, brain_region_id, single_neuron_synaptome_id, memodel_id):
    data = assert_request(
        client.get,
        url=f"{ROUTE}/{single_neuron_synaptome_id}",
    ).json()
    assert data["brain_region"]["id"] == str(brain_region_id), (
        f"Failed to get id for reconstruction morphology: {data}"
    )
    assert data["description"] == "my-description"
    assert data["name"] == "my-synaptome"
    assert data["me_model"]["id"] == str(memodel_id), f"Failed to get id frmo me model; {data}"
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


def test_pagination(db, client, brain_region_id, emodel_id, morphology_id, species_id):
    me_model_1 = add_db(
        db,
        MEModel(
            name="me-model-1",
            description="my-description-1",
            brain_region_id=brain_region_id,
            authorized_project_id=PROJECT_ID,
            emodel_id=emodel_id,
            morphology_id=morphology_id,
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
            morphology_id=morphology_id,
            species_id=species_id,
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
    )
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 3


@pytest.fixture
def faceted_ids(db, brain_region_hierarchy_name_id, create_memodel_ids: CreateIds):
    brain_region_ids = [
        create_brain_region(db, brain_region_hierarchy_name_id, hierarchy_id=i, name=f"region-{i}").id for i in range(2)
    ]
    memodel_ids = create_memodel_ids(2)
    single_simulation_synaptome_ids = [
        _create_single_neuron_synaptome_id(
            db,
            {
                "name": f"synaptome-{i}",
                "description": f"brain-region-{brain_region_id} me-model-{memodel_id}",
                "me_model_id": str(memodel_id),
                "seed": i,
                "brain_region_id": str(brain_region_id),
                "authorized_project_id": PROJECT_ID,
            },
        )
        for i, (memodel_id, brain_region_id) in enumerate(it.product(memodel_ids, brain_region_ids))
    ]
    return brain_region_ids, memodel_ids, single_simulation_synaptome_ids


def test_facets(client, faceted_ids):
    brain_region_ids, memodel_ids, _ = faceted_ids

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"with_facets": True},
    ).json()

    assert "facets" in data
    facets = data["facets"]

    assert facets["contribution"] == []
    assert facets["brain_region"] == [
        {"id": str(brain_region_ids[0]), "label": "region-0", "count": 2, "type": "brain_region"},
        {"id": str(brain_region_ids[1]), "label": "region-1", "count": 2, "type": "brain_region"},
    ]
    assert facets["me_model"] == [
        {
            "id": str(memodel_ids[0]),
            "label": "0",
            "count": 2,
            "type": "me_model",
        },
        {
            "id": str(memodel_ids[1]),
            "label": "1",
            "count": 2,
            "type": "me_model",
        },
    ]

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"search": f"me-model-{memodel_ids[0]}", "with_facets": True},
    ).json()

    assert "facets" in data
    facets = data["facets"]

    assert facets["me_model"] == [
        {
            "id": str(memodel_ids[0]),
            "label": "0",
            "count": 2,
            "type": "me_model",
        }
    ]

    assert facets["brain_region"] == [
        {"id": str(brain_region_ids[0]), "label": "region-0", "count": 1, "type": "brain_region"},
        {"id": str(brain_region_ids[1]), "label": "region-1", "count": 1, "type": "brain_region"},
    ]
