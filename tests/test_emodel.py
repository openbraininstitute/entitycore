import itertools as it
import uuid
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from .conftest import Ids
from .utils import (
    BEARER_TOKEN,
    MISSING_ID,
    MISSING_ID_COMPACT,
    PROJECT_HEADERS,
    assert_dict_equal,
    assert_request,
    create_reconstruction_morphology_id,
)

ROUTE = "/emodel"

CreateEModelIds = Callable[[int], list[uuid.UUID]]


@pytest.mark.usefixtures("skip_project_check")
def test_create_emodel(
    client: TestClient, species_id, strain_id, brain_region_id, exemplar_morphology_id
):
    response = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": "Test EModel Description",
            "name": "Test EModel Name",
            "iteration": "test iteration",
            "score": -1,
            "seed": -1,
            "exemplar_morphology_id": exemplar_morphology_id,
        },
    )
    data = response.json()
    assert_dict_equal(
        data,
        {
            "brain_region.id": brain_region_id,
            "species.id": species_id,
            "strain.id": strain_id,
        },
    )
    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )


@pytest.mark.usefixtures("skip_project_check")
def test_get_emodel(client: TestClient, create_emodel_ids: CreateEModelIds):
    emodel_id = str(create_emodel_ids(1)[0])
    response = assert_request(
        client.get,
        url=f"{ROUTE}/{emodel_id}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert_dict_equal(response.json(), {"id": emodel_id})


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
def test_query_emodel(client: TestClient, create_emodel_ids: CreateEModelIds):
    count = 11
    create_emodel_ids(count)

    response = assert_request(
        client.get,
        url=ROUTE,
        params={"page_size": 10},
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 10

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"page_size": 100},
    )
    data = response.json()["data"]
    assert len(data) == 11


@pytest.mark.usefixtures("skip_project_check")
def test_emodels_sorted(client: TestClient, create_emodel_ids: CreateEModelIds):
    count = 11
    emodel_ids = create_emodel_ids(count)

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"order_by": "+creation_date", "page_size": 100},
    )
    data = response.json()["data"]
    assert len(data) == count
    assert all(
        elem["creation_date"] > prev_elem["creation_date"] for prev_elem, elem in it.pairwise(data)
    )

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"order_by": "-creation_date"},
    )
    data = response.json()["data"]

    assert all(
        elem["creation_date"] < prev_elem["creation_date"] for prev_elem, elem in it.pairwise(data)
    )

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"order_by": "+creation_date", "page": 1, "page_size": 3},
    )
    data = response.json()["data"]
    assert len(data) == 3
    assert [row["id"] for row in data] == [str(id_) for id_ in emodel_ids][:3]


@pytest.mark.usefixtures("skip_project_check")
def test_facets(client: TestClient, create_faceted_emodel_ids: Ids):
    ids = create_faceted_emodel_ids

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"with_facets": True},
    )
    data = response.json()

    assert "facets" in data
    facets = data["facets"]

    assert facets == {
        "mtype": [],
        "etype": [],
        "species": [
            {"id": ids.species_ids[0], "label": "TestSpecies0", "count": 4, "type": "species"},
            {"id": ids.species_ids[1], "label": "TestSpecies1", "count": 4, "type": "species"},
        ],
        "contribution": [],
        "brain_region": [
            {"id": ids.brain_region_ids[0], "label": "region0", "count": 4, "type": "brain_region"},
            {"id": ids.brain_region_ids[1], "label": "region1", "count": 4, "type": "brain_region"},
        ],
        "exemplar_morphology": [
            {
                "id": ids.morphology_ids[0],
                "label": "test exemplar morphology 0",
                "count": 4,
                "type": "exemplar_morphology",
            },
            {
                "id": ids.morphology_ids[1],
                "label": "test exemplar morphology 1",
                "count": 4,
                "type": "exemplar_morphology",
            },
        ],
    }

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"search": f"species{ids.species_ids[0]}", "with_facets": True},
    )
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
        "contribution": [],
        "brain_region": [
            {"id": 0, "label": "region0", "count": 2, "type": "brain_region"},
            {"id": 1, "label": "region1", "count": 2, "type": "brain_region"},
        ],
        "exemplar_morphology": [
            {
                "id": ids.morphology_ids[0],
                "label": "test exemplar morphology 0",
                "count": 2,
                "type": "exemplar_morphology",
            },
            {
                "id": ids.morphology_ids[1],
                "label": "test exemplar morphology 1",
                "count": 2,
                "type": "exemplar_morphology",
            },
        ],
    }


@pytest.mark.usefixtures("skip_project_check")
def test_authorization(client, species_id, strain_id, brain_region_id, exemplar_morphology_id):
    emodel_json = {
        "brain_region_id": brain_region_id,
        "description": "morph description",
        "legacy_id": "Test Legacy ID",
        "name": "Test Morphology Name",
        "species_id": species_id,
        "strain_id": strain_id,
        "exemplar_morphology_id": exemplar_morphology_id,
        "score": 0,
        "iteration": "0",
        "seed": 0,
    }

    public_emodel = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=emodel_json
        | {
            "name": "public emodel",
            "authorized_public": True,
        },
    )
    public_emodel = public_emodel.json()

    assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN
        | {
            "virtual-lab-id": "42424242-4242-4000-9000-424242424242",
            "project-id": "42424242-4242-4000-9000-424242424242",
        },
        json=emodel_json,
        expected_status_code=403,
    )

    exemplar_morphology_id = create_reconstruction_morphology_id(
        client,
        species_id,
        strain_id,
        brain_region_id,
        headers=BEARER_TOKEN
        | {
            "virtual-lab-id": "42424242-4242-4000-9000-424242424242",
            "project-id": "42424242-4242-4000-9000-424242424242",
        },
        authorized_public=False,
    )

    inaccessible_obj = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN
        | {
            "virtual-lab-id": "42424242-4242-4000-9000-424242424242",
            "project-id": "42424242-4242-4000-9000-424242424242",
        },
        json=emodel_json
        | {"name": "inaccessible emodel", "exemplar_morphology_id": exemplar_morphology_id},
    )

    inaccessible_obj = inaccessible_obj.json()

    private_emodel0 = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=emodel_json | {"name": "private emodel 0"},
    )
    private_emodel0 = private_emodel0.json()

    private_emodel1 = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=emodel_json
        | {
            "name": "private emodel 1",
        },
    )
    private_emodel1 = private_emodel1.json()

    # only return results that matches the desired project, and public ones
    response = assert_request(client.get, url=ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS)
    data = response.json()["data"]
    assert len(data) == 3

    ids = {row["id"] for row in data}
    assert ids == {
        public_emodel["id"],
        private_emodel0["id"],
        private_emodel1["id"],
    }

    response = assert_request(
        client.get,
        url=f"{ROUTE}/{inaccessible_obj['id']}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        expected_status_code=404,
    )


@pytest.mark.usefixtures("skip_project_check")
def test_pagination(client, create_emodel_ids):
    total_items = 29
    create_emodel_ids(total_items)

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"page_size": total_items + 1},
    )

    assert len(response.json()["data"]) == total_items

    for i in range(1, total_items + 1):
        expected_items = i
        response = assert_request(
            client.get,
            url=ROUTE,
            headers=BEARER_TOKEN | PROJECT_HEADERS,
            params={"page_size": expected_items},
        )

        data = response.json()["data"]
        assert len(data) == expected_items

        assert [int(d["name"]) for d in data] == list(
            range(total_items - 1, total_items - expected_items - 1, -1)
        )

    items = []
    for i in range(1, total_items + 1):
        response = assert_request(
            client.get,
            url=ROUTE,
            headers=BEARER_TOKEN | PROJECT_HEADERS,
            params={"page": i, "page_size": 1},
        )

        data = response.json()["data"]
        assert len(data) == 1
        items.append(data[0])

    assert len(items) == total_items
    data_ids = [int(i["name"]) for i in items]
    assert list(reversed(data_ids)) == list(range(total_items))
