import itertools as it

import pytest

from app.db.model import MEModel, SingleNeuronSimulation
from app.db.types import AssetLabel, EntityType
from app.filters.single_neuron_simulation import SingleNeuronSimulationFilter

from .utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    PROJECT_ID,
    TEST_DATA_DIR,
    USER_SUB_ID_1,
    add_db,
    assert_request,
    check_authorization,
    check_brain_region_filter,
    check_entity_delete_one,
    check_entity_update_one,
    create_brain_region,
    upload_entity_asset,
)

FILE_EXAMPLE_PATH = TEST_DATA_DIR / "example.json"
ROUTE = "/single-neuron-simulation"
ADMIN_ROUTE = "/admin/single-neuron-simulation"


def _create_me_model_id(db, data):
    return add_db(db, MEModel(**data)).id


def _create_single_neuron_simulation_id(db, data):
    return add_db(db, SingleNeuronSimulation(**data)).id


@pytest.fixture
def single_neuron_simulation_id(client, memodel_id, brain_region_id):
    response = assert_request(
        client.post,
        url=ROUTE,
        json={
            "name": "foo",
            "description": "my-description",
            "injection_location": ["soma[0]"],
            "recording_location": ["soma[0]_0.5"],
            "me_model_id": memodel_id,
            "status": "done",
            "seed": 1,
            "authorized_public": False,
            "brain_region_id": str(brain_region_id),
        },
    )

    data = response.json()

    with FILE_EXAMPLE_PATH.open("rb") as f:
        upload_entity_asset(
            client,
            EntityType.single_neuron_simulation,
            data["id"],
            label=AssetLabel.single_neuron_simulation_data,
            files={"file": ("c.json", f, "application/json")},
        )

    return data["id"]


@pytest.fixture
def json_data(brain_region_id, memodel_id):
    return {
        "name": "original-sim",
        "description": "original-description",
        "injection_location": ["soma[0]"],
        "recording_location": ["soma[0]_0.5"],
        "me_model_id": memodel_id,
        "status": "done",
        "seed": 1,
        "authorized_public": False,
        "brain_region_id": str(brain_region_id),
    }


@pytest.fixture
def public_json_data(brain_region_id, public_memodel_id):
    return {
        "name": "original-sim",
        "description": "original-description",
        "injection_location": ["soma[0]"],
        "recording_location": ["soma[0]_0.5"],
        "me_model_id": public_memodel_id,
        "status": "done",
        "seed": 1,
        "authorized_public": True,
        "brain_region_id": str(brain_region_id),
    }


def test_update_one(clients, public_json_data):
    check_entity_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=public_json_data,
        patch_payload={
            "name": "name",
            "description": "description",
            "status": "error",
            "seed": 42,
            "injection_location": ["dendrite[0]"],
            "recording_location": ["dendrite[0]_0.5"],
        },
        optional_payload=None,
    )


def test_single_neuron_simulation(client, brain_region_id, memodel_id, single_neuron_simulation_id):
    response = assert_request(
        client.post,
        url=ROUTE,
        json={
            "name": "foo",
            "description": "my-description",
            "injection_location": ["soma[0]"],
            "recording_location": ["soma[0]_0.5"],
            "me_model_id": memodel_id,
            "status": "done",
            "seed": 1,
            "authorized_public": False,
            "brain_region_id": str(brain_region_id),
        },
    )

    data = response.json()

    with FILE_EXAMPLE_PATH.open("rb") as f:
        upload_entity_asset(
            client,
            EntityType.single_neuron_simulation,
            data["id"],
            label=AssetLabel.single_neuron_simulation_data,
            files={"file": ("c.json", f, "application/json")},
        )

    assert data["brain_region"]["id"] == str(brain_region_id), (
        f"Failed to get id for cell morphology: {data}"
    )
    assert data["description"] == "my-description"
    assert data["name"] == "foo"
    assert data["injection_location"] == ["soma[0]"]
    assert data["recording_location"] == ["soma[0]_0.5"]
    assert data["me_model"]["id"] == memodel_id, f"Failed to get id frmo me model; {data}"
    assert data["status"] == "done"
    assert data["authorized_project_id"] == PROJECT_ID
    assert data["type"] == EntityType.single_neuron_simulation
    assert data["created_by"]["id"] == data["updated_by"]["id"]
    assert data["authorized_public"] is False

    response = assert_request(client.get, url=f"{ROUTE}/{single_neuron_simulation_id}")
    data = response.json()
    assert data["brain_region"]["id"] == str(brain_region_id), (
        f"Failed to get id for cell morphology: {data}"
    )
    assert data["description"] == "my-description"
    assert data["name"] == "foo"
    assert data["injection_location"] == ["soma[0]"]
    assert data["recording_location"] == ["soma[0]_0.5"]
    assert data["me_model"]["id"] == memodel_id, f"Failed to get id frmo me model; {data}"
    assert data["status"] == "done"
    assert data["authorized_project_id"] == PROJECT_ID
    assert data["type"] == EntityType.single_neuron_simulation
    assert "assets" in data
    assert data["assets"][0]["label"] == AssetLabel.single_neuron_simulation_data
    assert data["created_by"]["id"] == data["updated_by"]["id"]
    assert data["authorized_public"] is False


def test_single_neuron_simulation__public(client, public_json_data):
    data = assert_request(
        client.post,
        url=ROUTE,
        json=public_json_data,
    ).json()
    assert data["authorized_public"] is True


def test_delete_one(db, clients, public_json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=public_json_data,
        expected_counts_before={
            SingleNeuronSimulation: 1,
            MEModel: 1,
        },
        expected_counts_after={
            SingleNeuronSimulation: 0,
            MEModel: 1,
        },
    )


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


def test_authorization(client_user_1, client_user_2, client_no_project, public_json_data):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, public_json_data)


def test_pagination(db, client, brain_region_id, emodel_id, morphology_id, species_id, person_id):
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
            created_by_id=person_id,
            updated_by_id=person_id,
            validation_status="created",
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
            created_by_id=person_id,
            updated_by_id=person_id,
            validation_status="created",
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
                status="done",
                seed=1,
                authorized_public=False,
                brain_region_id=brain_region_id,
                authorized_project_id=PROJECT_ID,
                created_by_id=person_id,
                updated_by_id=person_id,
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
def faceted_ids(db, brain_region_hierarchy_id, emodel_id, morphology_id, species_id, person_id):
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
                "created_by_id": str(person_id),
                "updated_by_id": str(person_id),
                "validation_status": "created",
            },
        )
        for i in range(2)
    ]
    single_simulation_synaptome_ids = [
        _create_single_neuron_simulation_id(
            db,
            {
                "name": f"sim-{i}",
                "description": f"sim-desc-{i}",
                "me_model_id": str(me_model_id),
                "status": "done",
                "injection_location": ["soma[0]"],
                "recording_location": ["soma[0]_0.5"],
                "seed": i,
                "brain_region_id": str(brain_region_id),
                "authorized_project_id": PROJECT_ID,
                "created_by_id": str(person_id),
                "updated_by_id": str(person_id),
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
        params={"me_model__name": "me-model-0", "with_facets": True},
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
    db, client, brain_region_hierarchy_id, species_id, emodel_id, morphology_id, person_id
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
                    "created_by_id": str(person_id),
                    "updated_by_id": str(person_id),
                    "validation_status": "created",
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
            status="done",
            seed=1,
            authorized_project_id=PROJECT_ID,
            created_by_id=person_id,
            updated_by_id=person_id,
        )

    check_brain_region_filter(ROUTE, client, db, brain_region_hierarchy_id, create_model_function)


def test_sorting_filtering(client, faceted_ids):
    n_models = len(faceted_ids[-1])

    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    for ordering_field in SingleNeuronSimulationFilter.Constants.ordering_model_fields:
        data = req({"name__in": ["sim-2", "sim-3"], "order_by": f"+{ordering_field}"})
        assert len(data) == 2

        data = req({"name__in": ["sim-2", "sim-3"], "order_by": f"-{ordering_field}"})
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

        data = req({"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1})
        assert len(data) == n_models

        data = req({"ilike_search": "sim-desc*", "order_by": ordering_field})
        assert len(data) == n_models

        data = req({"ilike_search": "sim-1", "order_by": ordering_field})
        assert len(data) == 1
