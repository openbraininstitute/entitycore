import itertools as it

import pytest

from app.db.model import MEModel, SingleNeuronSimulation
from app.db.types import AssetLabel, EntityType

from .utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    PROJECT_ID,
    add_db,
    assert_request,
    check_brain_region_filter,
    create_brain_region,
)
from tests.routers.test_asset import _upload_entity_asset

ROUTE = "/single-neuron-simulation"


def _create_me_model_id(db, data):
    return add_db(db, MEModel(**data)).id


def _create_single_neuron_simulation_id(db, data):
    return add_db(db, SingleNeuronSimulation(**data)).id


def test_single_neuron_simulation(client, brain_region_id, memodel_id):
    response = assert_request(
        client.post,
        url=ROUTE,
        json={
            "name": "foo",
            "description": "my-description",
            "injection_location": ["soma[0]"],
            "recording_location": ["soma[0]_0.5"],
            "me_model_id": memodel_id,
            "status": "success",
            "seed": 1,
            "authorized_public": False,
            "brain_region_id": str(brain_region_id),
        },
    )

    data = response.json()
    _upload_entity_asset(
        client,
        EntityType.single_neuron_simulation,
        data["id"],
        label=AssetLabel.single_cell_simulation_data,
    )
    assert data["brain_region"]["id"] == str(brain_region_id), (
        f"Failed to get id for reconstruction morphology: {data}"
    )
    assert data["description"] == "my-description"
    assert data["name"] == "foo"
    assert data["injection_location"] == ["soma[0]"]
    assert data["recording_location"] == ["soma[0]_0.5"]
    assert data["me_model"]["id"] == memodel_id, f"Failed to get id frmo me model; {data}"
    assert data["status"] == "success"
    assert data["authorized_project_id"] == PROJECT_ID
    assert data["type"] == EntityType.single_neuron_simulation

    response = assert_request(client.get, url=f"{ROUTE}/{data['id']}")
    data = response.json()
    assert data["brain_region"]["id"] == str(brain_region_id), (
        f"Failed to get id for reconstruction morphology: {data}"
    )
    assert data["description"] == "my-description"
    assert data["name"] == "foo"
    assert data["injection_location"] == ["soma[0]"]
    assert data["recording_location"] == ["soma[0]_0.5"]
    assert data["me_model"]["id"] == memodel_id, f"Failed to get id frmo me model; {data}"
    assert data["status"] == "success"
    assert data["authorized_project_id"] == PROJECT_ID
    assert data["type"] == EntityType.single_neuron_simulation
    assert "assets" in data
    assert data["assets"][0]["label"] == AssetLabel.single_cell_simulation_data


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


def test_authorization(
    client_user_1, client_user_2, client_no_project, memodel_id, brain_region_id
):
    json_data = {
        "name": "foo",
        "description": "my-description",
        "injection_location": ["soma[0]"],
        "recording_location": ["soma[0]_0.5"],
        "me_model_id": memodel_id,
        "status": "failure",
        "seed": 1,
        "brain_region_id": str(brain_region_id),
    }

    response = assert_request(
        client_user_1.post,
        url=ROUTE,
        json=json_data | {"name": "Public Entity", "authorized_public": True},
    )
    public_morph = response.json()

    inaccessible_obj = assert_request(
        client_user_2.post,
        url=ROUTE,
        json=json_data | {"name": "inaccessible morphology 1"},
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
        json=json_data | {"name": "private morphology 1"},
    )
    private_obj1 = private_obj1.json()

    # only return results that matches the desired project, and public ones
    response = assert_request(client_user_1.get, url=ROUTE)
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

    # only return public results
    response = client_no_project.get(ROUTE)
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
            holding_current=0,
            threshold_current=0,
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
            holding_current=0,
            threshold_current=0,
        ),
    )

    def create(count):
        ids = []
        for i, me_model in zip(range(count), it.cycle((me_model_1, me_model_2))):
            row = SingleNeuronSimulation(
                name=f"sim-{i}",
                description="my-description",
                injection_location=["soma[0]"],
                recording_location=["soma[0]_0.5"],
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

    response = assert_request(client.get, url=ROUTE, params={"page_size": 3})
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 3
    assert "assets" in response_json["data"][0]


@pytest.fixture
def faceted_ids(db, brain_region_hierarchy_id, emodel_id, morphology_id, species_id):
    brain_region_ids = [
        create_brain_region(
            db, brain_region_hierarchy_id, annotation_value=i, name=f"region-{i}"
        ).id
        for i in range(2)
    ]
    me_model_ids = [
        _create_me_model_id(
            db,
            {
                "name": f"me-model-{i}",
                "description": f"description-{i}",
                "brain_region_id": str(brain_region_ids[i]),
                "authorized_project_id": PROJECT_ID,
                "emodel_id": emodel_id,
                "morphology_id": morphology_id,
                "species_id": species_id,
                "holding_current": 0,
                "threshold_current": 0,
            },
        )
        for i in range(2)
    ]
    single_simulation_synaptome_ids = [
        _create_single_neuron_simulation_id(
            db,
            {
                "name": f"sim-{i}",
                "description": f"brain-region-{brain_region_id} me-model-{me_model_id}",
                "me_model_id": str(me_model_id),
                "status": "success",
                "injection_location": ["soma[0]"],
                "recording_location": ["soma[0]_0.5"],
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


def test_facets(client, faceted_ids):
    brain_region_ids, me_model_ids, _ = faceted_ids

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
        {"id": str(brain_region_ids[0]), "label": "region-0", "count": 1, "type": "brain_region"},
        {"id": str(brain_region_ids[1]), "label": "region-1", "count": 1, "type": "brain_region"},
    ]


def test_brain_region_filter(
    db, client, brain_region_hierarchy_id, species_id, emodel_id, morphology_id
):
    def create_model_function(db, name, brain_region_id):
        me_model_id = str(
            _create_me_model_id(
                db,
                {
                    "name": "me-model",
                    "description": "description",
                    "brain_region_id": brain_region_id,
                    "authorized_project_id": PROJECT_ID,
                    "emodel_id": emodel_id,
                    "morphology_id": morphology_id,
                    "species_id": species_id,
                    "holding_current": 0,
                    "threshold_current": 0,
                },
            )
        )

        return SingleNeuronSimulation(
            name=name,
            brain_region_id=brain_region_id,
            description="description",
            legacy_id="Test Legacy ID",
            injection_location=["soma[0]"],
            recording_location=["soma[0]_0.5"],
            me_model_id=me_model_id,
            status="success",
            seed=1,
            authorized_project_id=PROJECT_ID,
        )

    check_brain_region_filter(ROUTE, client, db, brain_region_hierarchy_id, create_model_function)
