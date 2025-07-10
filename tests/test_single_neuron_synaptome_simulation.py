import itertools as it
import uuid

import pytest

from app.db.model import Agent, MEModel, SingleNeuronSynaptome, SingleNeuronSynaptomeSimulation
from app.db.types import EntityType
from app.filters.single_neuron_synaptome_simulation import SingleNeuronSynaptomeSimulationFilter

from .utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    PROJECT_ID,
    add_db,
    assert_request,
    check_brain_region_filter,
    create_brain_region,
)

MODEL = SingleNeuronSynaptomeSimulation
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
    created_by_id: uuid.UUID,
    updated_by_id: uuid.UUID | None = None,
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
            created_by_id=created_by_id,
            updated_by_id=updated_by_id or created_by_id,
        ),
    ).id


@pytest.fixture
def synaptome_id(db, memodel_id, brain_region_id, person_id):
    return _create_synaptome_id(
        db,
        memodel_id=memodel_id,
        brain_region_id=brain_region_id,
        created_by_id=person_id,
    )


@pytest.fixture
def json_data(brain_region_id, synaptome_id):
    return {
        "name": "my-sim",
        "description": "my-description",
        "injection_location": ["soma[0]"],
        "recording_location": ["soma[0]_0.5"],
        "status": "success",
        "seed": 1,
        "synaptome_id": str(synaptome_id),
        "brain_region_id": str(brain_region_id),
        "authorized_public": False,
    }


def _create_simulation_id(
    client,
    *,
    synaptome_id,
    brain_region_id,
    name="my-synaptome-simulation",
    description="my-synaptome-simulation-description",
    injection_location=None,
    recording_location=None,
    status="success",
    seed=1,
    authorized_public=False,
):
    if injection_location is None:
        injection_location = ["soma[0]"]

    if recording_location is None:
        recording_location = ["soma[0]_0.5"]

    return assert_request(
        client.post,
        url=ROUTE,
        json={
            "name": name,
            "description": description,
            "injection_location": injection_location,
            "recording_location": recording_location,
            "status": status,
            "seed": seed,
            "synaptome_id": str(synaptome_id),
            "brain_region_id": str(brain_region_id),
            "authorized_public": authorized_public,
        },
    ).json()["id"]


@pytest.fixture
def simulation_id(client, json_data):
    return _create_simulation_id(client, **json_data)


def test_create_one(client, json_data, brain_region_id, synaptome_id):
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data,
    ).json()
    assert data["brain_region"]["id"] == str(brain_region_id)
    assert data["description"] == "my-description"
    assert data["name"] == "my-sim"
    assert data["status"] == "success"
    assert data["injection_location"] == ["soma[0]"]
    assert data["recording_location"] == ["soma[0]_0.5"]
    assert data["synaptome"]["id"] == str(synaptome_id)
    assert data["authorized_project_id"] == PROJECT_ID
    assert data["type"] == EntityType.single_neuron_synaptome_simulation
    assert data["created_by"]["id"] == data["updated_by"]["id"]
    assert data["authorized_public"] is False


def test_create_one__public(client, json_data):
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data | {"authorized_public": True},
    ).json()
    assert data["authorized_public"] is True


def test_read_one(client, brain_region_id, synaptome_id, simulation_id):
    data = assert_request(
        client.get,
        url=f"{ROUTE}/{simulation_id}",
    ).json()
    assert data["brain_region"]["id"] == str(brain_region_id)
    assert data["description"] == "my-description"
    assert data["name"] == "my-sim"
    assert data["status"] == "success"
    assert data["injection_location"] == ["soma[0]"]
    assert data["recording_location"] == ["soma[0]_0.5"]
    assert data["synaptome"]["id"] == str(synaptome_id)
    assert data["authorized_project_id"] == PROJECT_ID
    assert data["type"] == EntityType.single_neuron_synaptome_simulation
    assert data["created_by"]["id"] == data["updated_by"]["id"]
    assert data["authorized_public"] is False


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


def test_pagination(db, client, brain_region_id, memodel_id, person_id):
    synaptome_1_id = _create_synaptome_id(
        db,
        name="syn-1",
        memodel_id=memodel_id,
        brain_region_id=brain_region_id,
        created_by_id=person_id,
    )
    synaptome_2_id = _create_synaptome_id(
        db,
        name="syn-2",
        memodel_id=memodel_id,
        brain_region_id=brain_region_id,
        created_by_id=person_id,
    )

    def create(count):
        ids = []
        for i, synaptome_id in zip(range(count), it.cycle((synaptome_1_id, synaptome_2_id))):
            sim_id = _create_simulation_id(
                client,
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
def faceted_ids(db, client, brain_region_hierarchy_id, memodel_id, person_id):
    brain_region_ids = [
        create_brain_region(
            db,
            brain_region_hierarchy_id,
            annotation_value=i,
            name=f"region-{i}",
            created_by_id=person_id,
        ).id
        for i in range(2)
    ]
    synaptome_ids = [
        _create_synaptome_id(
            db,
            name=f"synaptome-{i}",
            description=f"description-{i}",
            brain_region_id=brain_region_ids[i],
            memodel_id=memodel_id,
            created_by_id=person_id,
        )
        for i in range(2)
    ]
    single_simulation_synaptome_ids = [
        _create_simulation_id(
            client,
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


def test_facets(db, client, faceted_ids):
    brain_region_ids, synaptome_ids, sim_ids = faceted_ids

    agent = db.get(Agent, db.get(MODEL, sim_ids[0]).created_by_id)

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
    assert facets["synaptome"] == [
        {
            "id": str(synaptome_ids[0]),
            "label": "synaptome-0",
            "count": 2,
            "type": "synaptome",
        },
        {
            "id": str(synaptome_ids[1]),
            "label": "synaptome-1",
            "count": 2,
            "type": "synaptome",
        },
    ]
    assert facets["created_by"] == [
        {"id": str(agent.id), "label": agent.pref_label, "count": 4, "type": agent.type}
    ]
    assert facets["updated_by"] == [
        {"id": str(agent.id), "label": agent.pref_label, "count": 4, "type": agent.type}
    ]

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"search": f"synaptome-{synaptome_ids[0]}", "with_facets": True},
    ).json()

    assert "facets" in data
    facets = data["facets"]

    assert facets["synaptome"] == [
        {
            "id": str(synaptome_ids[0]),
            "label": "synaptome-0",
            "count": 2,
            "type": "synaptome",
        }
    ]

    assert facets["brain_region"] == [
        {"id": str(brain_region_ids[0]), "label": "region-0", "count": 1, "type": "brain_region"},
        {"id": str(brain_region_ids[1]), "label": "region-1", "count": 1, "type": "brain_region"},
    ]
    assert facets["created_by"] == [
        {"id": str(agent.id), "label": agent.pref_label, "count": 2, "type": agent.type}
    ]
    assert facets["updated_by"] == [
        {"id": str(agent.id), "label": agent.pref_label, "count": 2, "type": agent.type}
    ]


def test_brain_region_filter(
    db, client, brain_region_hierarchy_id, species_id, emodel_id, morphology_id, person_id
):
    def create_model_function(db, name, brain_region_id):
        me_model_id = str(
            add_db(
                db,
                MEModel(
                    name=name,
                    description="description",
                    brain_region_id=brain_region_id,
                    authorized_project_id=PROJECT_ID,
                    emodel_id=emodel_id,
                    morphology_id=morphology_id,
                    species_id=species_id,
                    created_by_id=person_id,
                    updated_by_id=person_id,
                ),
            ).id
        )
        synaptome_id = str(
            add_db(
                db,
                SingleNeuronSynaptome(
                    name=name,
                    description="description",
                    me_model_id=me_model_id,
                    brain_region_id=brain_region_id,
                    seed=1,
                    authorized_project_id=PROJECT_ID,
                    created_by_id=person_id,
                    updated_by_id=person_id,
                ),
            ).id
        )

        return SingleNeuronSynaptomeSimulation(
            name=name,
            description="description",
            injection_location=["soma[0]"],
            recording_location=["soma[0]_0.5"],
            status="success",
            seed=1,
            synaptome_id=synaptome_id,
            brain_region_id=brain_region_id,
            authorized_project_id=PROJECT_ID,
            created_by_id=person_id,
            updated_by_id=person_id,
        )

    check_brain_region_filter(ROUTE, client, db, brain_region_hierarchy_id, create_model_function)


def test_sorting_filtering(client, faceted_ids):
    n_models = len(faceted_ids[-1])

    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    for ordering_field in SingleNeuronSynaptomeSimulationFilter.Constants.ordering_model_fields:
        data = req({"name__in": ["synaptome-2", "synaptome-3"], "order_by": f"+{ordering_field}"})
        assert len(data) == 2

        data = req({"name__in": ["synaptome-2", "synaptome-3"], "order_by": f"-{ordering_field}"})
        assert len(data) == 2

        data = req({"created_by__pref_label": "jd courcol", "order_by": ordering_field})
        assert len(data) == n_models

        data = req({"created_by__pref_label": "", "order_by": ordering_field})
        assert len(data) == 0

        data = req({"brain_region__name": "region-1", "order_by": ordering_field})
        assert all(d["brain_region"]["name"] == "region-1" for d in data)

        data = req({"brain_region__name": "", "order_by": ordering_field})
        assert len(data) == 0

        data = req({"brain_region__acronym": "acronym1", "order_by": ordering_field})
        assert all(d["brain_region"]["acronym"] == "acronym1" for d in data)

        data = req({"brain_region__acronym": "", "order_by": ordering_field})
        assert len(data) == 0
