import operator as op
import uuid
from unittest.mock import ANY

import pytest
from fastapi.testclient import TestClient

from app.db.model import MEModel
from app.filters.memodel import MEModelFilter
from app.schemas.me_model import MEModelRead

from .conftest import CreateIds, MEModels
from .utils import (
    PROJECT_ID,
    assert_request,
    check_brain_region_filter,
    create_reconstruction_morphology_id,
)

ROUTE = "/memodel"


def test_get_memodel(client: TestClient, memodel_id):
    response = client.get(f"{ROUTE}/{memodel_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == memodel_id
    assert "morphology" in data
    assert "emodel" in data
    assert "brain_region" in data
    assert "species" in data
    assert "strain" in data
    assert "mtypes" in data
    assert "etypes" in data
    MEModelRead.model_validate(data)


def test_missing(client):
    response = client.get(f"{ROUTE}/{uuid.uuid4()}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/notauuid")
    assert response.status_code == 422


@pytest.fixture
def json_data(brain_region_id, species_id, strain_id, morphology_id, emodel_id):
    return {
        "brain_region_id": str(brain_region_id),
        "species_id": species_id,
        "strain_id": strain_id,
        "description": "Test MEModel Description",
        "name": "Test MEModel Name",
        "morphology_id": morphology_id,
        "emodel_id": emodel_id,
        "authorized_public": False,
    }


def _assert_read_response(data, json_data):
    assert data["brain_region"]["id"] == json_data["brain_region_id"]
    assert data["species"]["id"] == json_data["species_id"]
    assert data["strain"]["id"] == json_data["strain_id"]
    assert "assets" in data["emodel"]
    assert "assets" in data["morphology"]
    assert data["created_by"]["id"] == data["updated_by"]["id"]
    assert data["authorized_public"] is json_data["authorized_public"]


def test_create_memodel(
    client: TestClient,
    json_data,
):
    response = client.post(ROUTE, json=json_data)
    assert response.status_code == 200, f"Failed to create memodel: {response.text}"
    data = response.json()
    _assert_read_response(data, json_data)

    response = client.get(f"{ROUTE}/{data['id']}")
    assert response.status_code == 200, f"Failed to get morphologys: {response.text}"
    data = response.json()
    _assert_read_response(data, json_data)

    response = client.get(ROUTE)
    assert response.status_code == 200, f"Failed to get morphologys: {response.text}"
    data = response.json()["data"][0]
    _assert_read_response(data, json_data)


def test_facets(client: TestClient, faceted_memodels: MEModels):
    ids = faceted_memodels

    response = client.get(
        ROUTE,
        params={"with_facets": True},
    )
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]

    assert facets == {
        "mtype": [],
        "etype": [],
        "strain": [],
        "species": [
            {
                "id": ids.species_ids[0],
                "label": "TestSpecies0",
                "count": 8,
                "type": "species",
            },
            {
                "id": ids.species_ids[1],
                "label": "TestSpecies1",
                "count": 8,
                "type": "species",
            },
        ],
        "contribution": [
            {
                "id": ids.agent_ids[0],
                "label": "test_organization_1",
                "count": 16,
                "type": "organization",
            },
            {
                "id": ids.agent_ids[1],
                "label": "test_person_1",
                "count": 16,
                "type": "person",
            },
        ],
        "brain_region": [
            {
                "id": str(ids.brain_region_ids[0]),
                "label": "region0",
                "count": 8,
                "type": "brain_region",
            },
            {
                "id": str(ids.brain_region_ids[1]),
                "label": "region1",
                "count": 8,
                "type": "brain_region",
            },
        ],
        "morphology": [
            {
                "id": ids.morphology_ids[0],
                "label": "test morphology 0",
                "count": 8,
                "type": "morphology",
            },
            {
                "id": ids.morphology_ids[1],
                "label": "test morphology 1",
                "count": 8,
                "type": "morphology",
            },
        ],
        "emodel": [
            {
                "id": ids.emodel_ids[0],
                "label": "0",
                "count": 8,
                "type": "emodel",
            },
            {
                "id": ids.emodel_ids[1],
                "label": "1",
                "count": 8,
                "type": "emodel",
            },
        ],
        "created_by": [{"id": ANY, "label": "test_person_1", "count": 16, "type": "person"}],
        "updated_by": [{"id": ANY, "label": "test_person_1", "count": 16, "type": "person"}],
    }


def test_filtered_facets(client: TestClient, faceted_memodels: MEModels):
    ids = faceted_memodels

    response = client.get(
        ROUTE,
        params={
            "species__id": ids.species_ids[0],
            "emodel__name__ilike": "%0%",
            "with_facets": True,
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]
    assert facets == {
        "mtype": [],
        "etype": [],
        "species": [
            {
                "id": ids.species_ids[0],
                "label": "TestSpecies0",
                "count": 4,
                "type": "species",
            }
        ],
        "strain": [],
        "contribution": [
            {
                "id": ids.agent_ids[0],
                "label": "test_organization_1",
                "count": 4,
                "type": "organization",
            },
            {
                "id": ids.agent_ids[1],
                "label": "test_person_1",
                "count": 4,
                "type": "person",
            },
        ],
        "brain_region": [
            {
                "id": str(ids.brain_region_ids[0]),
                "label": "region0",
                "count": 2,
                "type": "brain_region",
            },
            {
                "id": str(ids.brain_region_ids[1]),
                "label": "region1",
                "count": 2,
                "type": "brain_region",
            },
        ],
        "morphology": [
            {
                "id": ids.morphology_ids[0],
                "label": "test morphology 0",
                "count": 2,
                "type": "morphology",
            },
            {
                "id": ids.morphology_ids[1],
                "label": "test morphology 1",
                "count": 2,
                "type": "morphology",
            },
        ],
        "emodel": [
            {
                "id": ids.emodel_ids[0],
                "label": "0",
                "count": 4,
                "type": "emodel",
            }
        ],
        "created_by": [{"id": ANY, "label": "test_person_1", "count": 4, "type": "person"}],
        "updated_by": [{"id": ANY, "label": "test_person_1", "count": 4, "type": "person"}],
    }


def test_facets_with_search(client: TestClient, faceted_memodels: MEModels):
    ids = faceted_memodels

    response = client.get(
        ROUTE,
        params={"search": "foo", "with_facets": True},
    )
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]
    assert facets == {
        "mtype": [],
        "etype": [],
        "species": [
            {
                "id": ids.species_ids[0],
                "label": "TestSpecies0",
                "count": 8,
                "type": "species",
            }
        ],
        "strain": [],
        "contribution": [
            {
                "id": ids.agent_ids[0],
                "label": "test_organization_1",
                "count": 8,
                "type": "organization",
            },
            {
                "id": ids.agent_ids[1],
                "label": "test_person_1",
                "count": 8,
                "type": "person",
            },
        ],
        "brain_region": [
            {
                "id": str(ids.brain_region_ids[0]),
                "label": "region0",
                "count": 4,
                "type": "brain_region",
            },
            {
                "id": str(ids.brain_region_ids[1]),
                "label": "region1",
                "count": 4,
                "type": "brain_region",
            },
        ],
        "morphology": [
            {
                "id": ids.morphology_ids[0],
                "label": "test morphology 0",
                "count": 4,
                "type": "morphology",
            },
            {
                "id": ids.morphology_ids[1],
                "label": "test morphology 1",
                "count": 4,
                "type": "morphology",
            },
        ],
        "emodel": [
            {
                "id": ids.emodel_ids[0],
                "label": "0",
                "count": 4,
                "type": "emodel",
            },
            {
                "id": ids.emodel_ids[1],
                "label": "1",
                "count": 4,
                "type": "emodel",
            },
        ],
        "created_by": [{"id": ANY, "label": "test_person_1", "count": 8, "type": "person"}],
        "updated_by": [{"id": ANY, "label": "test_person_1", "count": 8, "type": "person"}],
    }


def test_pagination(client, create_memodel_ids: CreateIds):
    total_items = 3
    create_memodel_ids(total_items)

    response = client.get(ROUTE, params={"page_size": total_items + 1})

    assert response.status_code == 200
    assert len(response.json()["data"]) == total_items

    for i in range(1, total_items + 1):
        expected_items = i
        response = client.get(ROUTE, params={"page_size": expected_items})

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == expected_items

        assert [int(d["name"]) for d in data] == list(
            range(total_items - 1, total_items - expected_items - 1, -1)
        )

    items = []
    for i in range(1, total_items + 1):
        response = client.get(ROUTE, params={"page": i, "page_size": 1})

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        items.append(data[0])

    assert len(items) == total_items
    data_ids = [int(i["name"]) for i in items]
    assert list(reversed(data_ids)) == list(range(total_items))


def test_query_memodel(client: TestClient, create_memodel_ids: CreateIds):
    count = 11
    create_memodel_ids(count)

    response = client.get(
        ROUTE,
        params={"page_size": 10},
    )
    assert response.status_code == 200
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 10

    response = client.get(
        ROUTE,
        params={"page_size": 100},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 11
    assert data == sorted(data, key=op.itemgetter("creation_date"), reverse=True)


def test_sorted(client: TestClient, create_memodel_ids: CreateIds):
    count = 10
    create_memodel_ids(count)

    response = client.get(
        ROUTE,
        params={"order_by": "-name"},
    )
    assert response.status_code == 200
    data = response.json()["data"]

    assert data == sorted(data, key=op.itemgetter("name"), reverse=True)


def test_filter_memodel(client: TestClient, faceted_memodels: MEModels):
    morphologys = faceted_memodels

    response = client.get(
        ROUTE,
        params={
            "species__id": morphologys.species_ids[0],
            "emodel__name__ilike": "%0%",
        },
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["facets"] is None
    assert "data" in response_json

    data = response_json["data"]

    assert all(d["species"]["id"] == morphologys.species_ids[0] for d in data)
    assert all(d["emodel"]["name"] == "0" for d in data)


def test_memodel_search(client: TestClient, faceted_memodels: MEModels):  # noqa: ARG001
    response = client.get(
        ROUTE,
        params={"search": "foo"},
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["facets"] is None
    assert "data" in response_json

    data = response_json["data"]

    assert all(d["description"] == "foo" for d in data)


def test_authorization(
    client_user_1: TestClient,
    client_user_2: TestClient,
    species_id,
    strain_id,
    brain_region_id,
    morphology_id,
    emodel_id,
):
    public_morphology_id = create_reconstruction_morphology_id(
        client_user_1, species_id, strain_id, brain_region_id, authorized_public=True
    )

    # Different user but public accessible
    public_emodel_id = client_user_2.post(
        "/emodel",
        json={
            "brain_region_id": str(brain_region_id),
            "description": "morph description",
            "legacy_id": "Test Legacy ID",
            "name": "Test Morphology Name",
            "species_id": species_id,
            "strain_id": strain_id,
            "exemplar_morphology_id": public_morphology_id,
            "score": 0,
            "iteration": "0",
            "seed": 0,
            "authorized_public": True,
        },
    ).json()["id"]

    json = {
        "brain_region_id": str(brain_region_id),
        "description": "description",
        "legacy_id": "Test Legacy ID",
        "name": "Test name",
        "species_id": species_id,
        "strain_id": strain_id,
        "emodel_id": emodel_id,
        "morphology_id": morphology_id,
    }

    public_obj = client_user_1.post(
        ROUTE,
        json=json
        | {"emodel_id": public_emodel_id, "morphology_id": public_morphology_id}
        | {
            "name": "public obj",
            "authorized_public": True,
        },
    )
    assert public_obj.status_code == 200
    public_obj = public_obj.json()

    unauthorized_relations = client_user_2.post(
        ROUTE,
        json=json,
    )

    assert unauthorized_relations.status_code == 403

    unauthorized_public_with_private_relations = client_user_1.post(
        ROUTE,
        json=json | {"authorized_public": True},
    )

    assert unauthorized_public_with_private_relations.status_code == 403

    morphology_id = create_reconstruction_morphology_id(
        client_user_2,
        species_id,
        strain_id,
        str(brain_region_id),
        authorized_public=False,
    )

    unauthorized_emodel = client_user_2.post(
        ROUTE,
        json=json | {"morphology_id": morphology_id},
    )

    assert unauthorized_emodel.status_code == 403

    morphology_id_2 = (
        client_user_2.post(
            "/reconstruction-morphology",
            json={
                "name": "test",
                "description": "test",
                "species_id": species_id,
                "strain_id": strain_id,
                "brain_region_id": str(brain_region_id),
                "location": None,
                "legacy_id": None,
                "authorized_public": True,
            },
        )
    ).json()["id"]

    emodel_id = (
        client_user_2.post(
            "/emodel",
            json={
                "brain_region_id": str(brain_region_id),
                "species_id": species_id,
                "exemplar_morphology_id": morphology_id_2,
                "description": "test",
                "name": "test",
                "iteration": "test",
                "seed": 0,
                "score": 0,
                "authorized_public": True,
            },
        )
    ).json()["id"]

    inaccessible_obj = client_user_2.post(
        ROUTE,
        json=json | {"morphology_id": morphology_id_2, "emodel_id": emodel_id},
    )

    assert inaccessible_obj.status_code == 200

    inaccessible_obj = inaccessible_obj.json()

    # Public reference from private entity authorized
    private_obj0 = client_user_1.post(
        ROUTE,
        json=json
        | {
            "name": "private obj 0",
            "morphology_id": public_morphology_id,
            "emodel_id": public_emodel_id,
        },
    )
    assert private_obj0.status_code == 200
    private_obj0 = private_obj0.json()

    private_obj1 = client_user_1.post(
        ROUTE,
        json=json
        | {
            "name": "private obj 1",
        },
    )
    assert private_obj1.status_code == 200
    private_obj1 = private_obj1.json()

    public_obj_diff_project = client_user_1.post(
        ROUTE,
        json=json
        | {
            "morphology_id": morphology_id_2,
            "emodel_id": emodel_id,
            "authorized_public": True,
        },
    )

    assert public_obj_diff_project.status_code == 200

    public_obj_diff_project = public_obj_diff_project.json()

    # only return results that matches the desired project, and public ones
    response = client_user_1.get(ROUTE)
    data = response.json()["data"]
    assert len(data) == 4

    ids = {row["id"] for row in data}
    assert ids == {
        public_obj["id"],
        private_obj0["id"],
        private_obj1["id"],
        public_obj_diff_project["id"],
    }

    response = client_user_1.get(f"{ROUTE}/{inaccessible_obj['id']}")

    assert response.status_code == 404


def test_brain_region_filter(
    db, client, brain_region_hierarchy_id, species_id, morphology_id, emodel_id, person_id
):
    def create_model_function(_db, name, brain_region_id):
        return MEModel(
            name=name,
            brain_region_id=brain_region_id,
            species_id=species_id,
            strain_id=None,
            description="Test MEModel Description",
            morphology_id=morphology_id,
            emodel_id=emodel_id,
            authorized_project_id=PROJECT_ID,
            created_by_id=person_id,
            updated_by_id=person_id,
        )

    check_brain_region_filter(ROUTE, client, db, brain_region_hierarchy_id, create_model_function)


def test_sorting_filtering(client, faceted_memodels):
    n_models = len(faceted_memodels.memodels)

    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    for ordering_field in MEModelFilter.Constants.ordering_model_fields:
        data = req({"name__in": ["m-2", "m-3"], "order_by": f"+{ordering_field}"})
        assert len(data) == 2

        data = req({"name__in": ["m-2", "m-3"], "order_by": f"-{ordering_field}"})
        assert len(data) == 2

        data = req({"created_by__pref_label": "test_person_1", "order_by": ordering_field})
        assert len(data) == n_models

        data = req({"created_by__pref_label": "", "order_by": ordering_field})
        assert len(data) == 0

        data = req({"brain_region__name": "region0", "order_by": ordering_field})
        assert all(d["brain_region"]["name"] == "region0" for d in data)

        data = req({"brain_region__name": "", "order_by": ordering_field})
        assert len(data) == 0

        data = req({"brain_region__acronym": "acronym1", "order_by": ordering_field})
        assert all(d["brain_region"]["acronym"] == "acronym1" for d in data)

        data = req({"brain_region__acronym": "", "order_by": ordering_field})
        assert len(data) == 0

    data = req({"brain_region__name": "region0", "order_by": "-name"})
    assert all(d["brain_region"]["name"] == "region0" for d in data)
    assert [d["name"] for d in data] == ["m-9", "m-8", "m-3", "m-2", "m-11", "m-10", "m-1", "m-0"]
