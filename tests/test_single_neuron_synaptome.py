import itertools as it

import pytest

from app.db.model import (
    Agent,
    Contribution,
    MEModel,
    SingleNeuronSynaptome,
)
from app.db.types import EntityType
from app.filters.single_neuron_synaptome import SingleNeuronSynaptomeFilter

from .utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    PROJECT_ID,
    add_db,
    assert_request,
    check_authorization,
    check_brain_region_filter,
    count_db_class,
    create_brain_region,
)
from tests.conftest import CreateIds

MODEL = SingleNeuronSynaptome
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


def _assert_read_response(data, json_data):
    assert data["brain_region"]["id"] == json_data["brain_region_id"]
    assert data["description"] == "my-description"
    assert data["name"] == "my-synaptome"
    assert data["me_model"]["id"] == json_data["me_model_id"]
    assert data["authorized_project_id"] == PROJECT_ID
    assert len(data["contributions"]) == 2
    assert len(data["me_model"]["mtypes"]) == 1
    assert len(data["me_model"]["etypes"]) == 1
    assert data["created_by"]["id"] == data["updated_by"]["id"]
    assert data["type"] == EntityType.single_neuron_synaptome
    assert "assets" in data


def _assert_create_response(data, json_data):
    assert data["brain_region"]["id"] == json_data["brain_region_id"]
    assert data["description"] == "my-description"
    assert data["name"] == "my-synaptome"
    assert data["me_model"]["id"] == json_data["me_model_id"]
    assert data["authorized_project_id"] == PROJECT_ID
    assert data["created_by"]["id"] == data["updated_by"]["id"]


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


@pytest.fixture
def model_id(db, create_id, agents):
    model_id = create_id()

    agent_1, agent_2, role = agents
    add_db(
        db,
        Contribution(
            agent_id=agent_1.id,
            role_id=role.id,
            entity_id=model_id,
            created_by_id=agent_2.id,
            updated_by_id=agent_2.id,
        ),
    )
    add_db(
        db,
        Contribution(
            agent_id=agent_2.id,
            role_id=role.id,
            entity_id=model_id,
            created_by_id=agent_2.id,
            updated_by_id=agent_2.id,
        ),
    )

    return str(model_id)


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_create_response(data, json_data)


def test_read_one(client, model_id, json_data):
    data = assert_request(
        client.get,
        url=f"{ROUTE}/{model_id}",
    ).json()
    _assert_read_response(data, json_data)


def test_read_many(client, model_id, json_data):
    items = assert_request(
        client.get,
        url=f"{ROUTE}",
    ).json()["data"]
    assert len(items) == 1
    assert items[0]["id"] == model_id
    _assert_read_response(items[0], json_data)


def test_delete_one(db, client, client_admin, model_id):
    assert count_db_class(db, SingleNeuronSynaptome) == 1
    assert count_db_class(db, MEModel) == 1
    assert count_db_class(db, Contribution) == 6

    data = assert_request(client.delete, url=f"{ROUTE}/{model_id}", expected_status_code=403).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    data = assert_request(client_admin.delete, url=f"{ROUTE}/{model_id}").json()
    assert data["id"] == str(model_id)

    assert count_db_class(db, SingleNeuronSynaptome) == 0
    assert count_db_class(db, MEModel) == 1
    assert count_db_class(db, Contribution) == 4


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
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


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
        ),
    )

    def create(count):
        ids = []
        for i, me_model in zip(range(count), it.cycle((me_model_1, me_model_2))):
            row = SingleNeuronSynaptome(
                name=f"synaptome-{i}",
                description="my-description",
                me_model_id=me_model.id,
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
def faceted_ids(db, brain_region_hierarchy_id, create_memodel_ids: CreateIds, create_id, person_id):
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
    memodel_ids = create_memodel_ids(2)
    single_simulation_synaptome_ids = [
        create_id(
            name=f"synaptome-{i}",
            description=f"brain-region-{brain_region_id} me-model-{memodel_id}",
            me_model_id=str(memodel_id),
            seed=i,
            brain_region_id=str(brain_region_id),
        )
        for i, (memodel_id, brain_region_id) in enumerate(it.product(memodel_ids, brain_region_ids))
    ]
    return brain_region_ids, memodel_ids, single_simulation_synaptome_ids


def test_facets(db, client, faceted_ids):
    brain_region_ids, memodel_ids, syn_ids = faceted_ids

    agent = db.get(Agent, db.get(MODEL, syn_ids[0]).created_by_id)

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"with_facets": True},
    ).json()

    assert "facets" in data
    facets = data["facets"]
    assert facets == {
        "brain_region": [
            {
                "id": str(brain_region_ids[0]),
                "label": "region-0",
                "count": 2,
                "type": "brain_region",
            },
            {
                "id": str(brain_region_ids[1]),
                "label": "region-1",
                "count": 2,
                "type": "brain_region",
            },
        ],
        "contribution": [],
        "me_model": [
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
        ],
        "created_by": [
            {"id": str(agent.id), "label": agent.pref_label, "count": 4, "type": agent.type}
        ],
        "updated_by": [
            {"id": str(agent.id), "label": agent.pref_label, "count": 4, "type": agent.type}
        ],
    }

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
        },
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

        return SingleNeuronSynaptome(
            name=name,
            description="my-description",
            me_model_id=me_model_id,
            seed=1,
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

    for ordering_field in SingleNeuronSynaptomeFilter.Constants.ordering_model_fields:
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
