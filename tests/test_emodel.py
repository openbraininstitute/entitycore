import itertools as it

import pytest

from .utils import BEARER_TOKEN, PROJECT_HEADERS, create_reconstruction_morphology_id

ROUTE = "/emodel"


@pytest.mark.usefixtures("skip_project_check")
def test_create_emodel(client, species_id, strain_id, brain_region_id, exemplar_morphology_id):
    response = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": "Test EModel Description",
            "name": "Test EModel Name",
            "legacy_id": "Test Legacy ID",
            "iteration": "test iteration",
            "score": -1,
            "seed": -1,
            "exemplar_morphology_id": exemplar_morphology_id,
        },
    )
    assert response.status_code == 200, f"Failed to create emodel: {response.text}"
    data = response.json()
    assert data["brain_region"]["id"] == brain_region_id, f"Failed to get id for emodel: {data}"
    assert data["species"]["id"] == species_id, f"Failed to get species_id for emodel: {data}"
    assert data["strain"]["id"] == strain_id, f"Failed to get strain_id for emodel: {data}"

    response = client.get(ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 200, f"Failed to get emodels: {response.text}"


@pytest.mark.usefixtures("skip_project_check")
def test_missing(client):
    response = client.get(f"{ROUTE}/42424242", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/notanumber", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 422


@pytest.mark.usefixtures("skip_project_check")
def test_query_emodel(client, create_emodel_ids):
    count = 11
    create_emodel_ids(count)

    response = client.get(
        ROUTE,
        params={"page_size": 10},
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert response.status_code == 200
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 10

    response = client.get(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"page_size": 100},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 11


@pytest.mark.usefixtures("skip_project_check")
def test_emodels_sorted(client, create_emodel_ids):
    count = 11
    create_emodel_ids(count)

    response = client.get(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"order_by": "+creation_date", "page_size": 100},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == count
    assert all(
        elem["creation_date"] > prev_elem["creation_date"] for prev_elem, elem in it.pairwise(data)
    )

    response = client.get(
        ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS, params={"order_by": "-creation_date"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert all(
        elem["creation_date"] < prev_elem["creation_date"] for prev_elem, elem in it.pairwise(data)
    )

    response = client.get(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"order_by": "+creation_date", "page": 1, "page_size": 3},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 3
    assert [row["id"] for row in data] == [4, 5, 6]  # 1 2 3 are morphology and agents


@pytest.mark.usefixtures("skip_project_check")
def test_facets(client, create_faceted_emodel_ids):  # noqa: ARG001
    response = client.get(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"with_facets": True},
    )
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]

    assert facets == {
        "mtype": [],
        "etype": [],
        "species": [
            {"id": 1, "label": "TestSpecies0", "count": 4, "type": "species"},
            {"id": 2, "label": "TestSpecies1", "count": 4, "type": "species"},
        ],
        "contribution": [],
        "brain_region": [
            {"id": 0, "label": "region0", "count": 4, "type": "brain_region"},
            {"id": 1, "label": "region1", "count": 4, "type": "brain_region"},
        ],
        "exemplar_morphology": [
            {"id": 1, "label": "Test Morphology Name", "count": 4, "type": "exemplar_morphology"},
            {"id": 2, "label": "Test Morphology Name", "count": 4, "type": "exemplar_morphology"},
        ],
    }

    response = client.get(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"search": "species1", "with_facets": True},
    )
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]
    assert facets == {
        "mtype": [],
        "etype": [],
        "species": [{"id": 1, "label": "TestSpecies0", "count": 4, "type": "species"}],
        "contribution": [],
        "brain_region": [
            {"id": 0, "label": "region0", "count": 2, "type": "brain_region"},
            {"id": 1, "label": "region1", "count": 2, "type": "brain_region"},
        ],
        "exemplar_morphology": [
            {"id": 1, "label": "Test Morphology Name", "count": 2, "type": "exemplar_morphology"},
            {"id": 2, "label": "Test Morphology Name", "count": 2, "type": "exemplar_morphology"},
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

    public_emodel = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=emodel_json
        | {
            "name": "public emodel",
            "authorized_public": True,
        },
    )
    assert public_emodel.status_code == 200
    public_emodel = public_emodel.json()

    unauthorized_exemplar_morphology = client.post(
        ROUTE,
        headers=BEARER_TOKEN
        | {
            "virtual-lab-id": "42424242-4242-4000-9000-424242424242",
            "project-id": "42424242-4242-4000-9000-424242424242",
        },
        json=emodel_json,
    )

    assert unauthorized_exemplar_morphology.status_code == 403

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

    inaccessible_obj = client.post(
        ROUTE,
        headers=BEARER_TOKEN
        | {
            "virtual-lab-id": "42424242-4242-4000-9000-424242424242",
            "project-id": "42424242-4242-4000-9000-424242424242",
        },
        json=emodel_json
        | {"name": "inaccessible emodel", "exemplar_morphology_id": exemplar_morphology_id},
    )

    assert inaccessible_obj.status_code == 200

    inaccessible_obj = inaccessible_obj.json()

    private_emodel0 = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=emodel_json | {"name": "private emodel 0"},
    )
    assert private_emodel0.status_code == 200
    private_emodel0 = private_emodel0.json()

    private_emodel1 = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=emodel_json
        | {
            "name": "private emodel 1",
        },
    )
    assert private_emodel1.status_code == 200
    private_emodel1 = private_emodel1.json()

    # only return results that matches the desired project, and public ones
    response = client.get(ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS)
    data = response.json()["data"]
    assert len(data) == 3

    ids = {row["id"] for row in data}
    assert ids == {
        public_emodel["id"],
        private_emodel0["id"],
        private_emodel1["id"],
    }

    response = client.get(
        f"{ROUTE}/{inaccessible_obj['id']}", headers=BEARER_TOKEN | PROJECT_HEADERS
    )

    assert response.status_code == 404


@pytest.mark.usefixtures("skip_project_check")
def test_pagination(client, create_emodel_ids):
    total_items = 29
    create_emodel_ids(total_items)
    db_id_offset = 4  # db indexes start from 4 due to the created morphology and agents

    response = client.get(
        ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS, params={"page_size": total_items + 1}
    )

    assert response.status_code == 200
    assert len(response.json()["data"]) == total_items

    for i in range(1, total_items + 1):
        expected_items = i
        response = client.get(
            ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS, params={"page_size": expected_items}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == expected_items

        assert [d["id"] - db_id_offset for d in data] == list(
            range(total_items - 1, total_items - expected_items - 1, -1)
        )

    items = []
    for i in range(1, total_items + 1):
        response = client.get(
            ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS, params={"page": i, "page_size": 1}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        items.append(data[0])

    assert len(items) == total_items
    data_ids = [i["id"] - db_id_offset for i in items]
    assert list(reversed(data_ids)) == list(range(total_items))
