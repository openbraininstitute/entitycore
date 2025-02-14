import itertools as it

import pytest

from .utils import BEARER_TOKEN, PROJECT_HEADERS

ROUTE = "/reconstruction_morphology/"


@pytest.mark.usefixtures("skip_project_check")
def test_create_reconstruction_morphology(
    client, species_id, strain_id, license_id, brain_region_id
):
    morph_description = "Test Morphology Description"
    morph_name = "Test Morphology Name"
    response = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": morph_description,
            "name": morph_name,
            "brain_location": {"x": 10, "y": 20, "z": 30},
            "legacy_id": "Test Legacy ID",
            "license_id": license_id,
        },
    )
    assert (
        response.status_code == 200
    ), f"Failed to create reconstruction morphology: {response.text}"
    data = response.json()
    assert (
        data["brain_region"]["id"] == brain_region_id
    ), f"Failed to get id for reconstruction morphology: {data}"
    assert (
        data["species"]["id"] == species_id
    ), f"Failed to get species_id for reconstruction morphology: {data}"
    assert (
        data["strain"]["id"] == strain_id
    ), f"Failed to get strain_id for reconstruction morphology: {data}"
    assert (
        data["description"] == morph_description
    ), f"Failed to get description for reconstruction morphology: {data}"
    assert data["name"] == morph_name, f"Failed to get name for reconstruction morphology: {data}"
    assert (
        data["license"]["name"] == "Test License"
    ), f"Failed to get license for reconstruction morphology: {data}"

    response = client.get(ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert (
        response.status_code == 200
    ), f"Failed to get reconstruction morphologies: {response.text}"


@pytest.mark.usefixtures("skip_project_check")
def test_missing(client):
    response = client.get(ROUTE + "42424242", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 404

    response = client.get(ROUTE + "notanumber", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 422


@pytest.mark.usefixtures("skip_project_check")
def test_query_reconstruction_morphology(
    client, species_id, strain_id, brain_region_id, license_id
):
    def create_morphologies(nb_morph):
        for i in range(nb_morph):
            morph_description = f"Test Morphology Description {i}"
            morph_name = f"Test Morphology Name {i}"
            response = client.post(
                ROUTE,
                headers=BEARER_TOKEN | PROJECT_HEADERS,
                json={
                    "brain_region_id": brain_region_id,
                    "species_id": species_id,
                    "strain_id": strain_id,
                    "description": morph_description,
                    "name": morph_name,
                    "brain_location": {"x": 10, "y": 20, "z": 30},
                    "legacy_id": "Test Legacy ID",
                    "license_id": license_id,
                },
            )
            assert (
                response.status_code == 200
            ), f"Failed to create reconstruction morphology: {response.text}"

    count = 11
    create_morphologies(count)

    response = client.get(ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 10

    response = client.get(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"order_by": "+creation_date", "page_size": 100},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 11

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
        "/reconstruction_morphology/",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        params={"order_by": "+creation_date", "page": 0, "page_size": 3},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 3
    assert [row["id"] for row in data] == [1, 2, 3]

    response = client.get(ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]
    assert facets == {
        "species": [{"id": 1, "label": "Test Species", "count": count, "type": "species"}],
        "strain": [{"id": 1, "label": "Test Strain", "count": count, "type": "strain"}],
        "contributors": [],
    }

    response = client.get(ROUTE + "?search=Test", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]
    assert facets == {
        "species": [{"id": 1, "label": "Test Species", "count": count, "type": "species"}],
        "strain": [{"id": 1, "label": "Test Strain", "count": count, "type": "strain"}],
        "contributors": [],
    }


@pytest.mark.usefixtures("skip_project_check")
def test_authorization(client, species_id, strain_id, license_id, brain_region_id):
    morph_json = {
        "brain_location": {"x": 10, "y": 20, "z": 30},
        "brain_region_id": brain_region_id,
        "description": "morph description",
        "legacy_id": "Test Legacy ID",
        "license_id": license_id,
        "name": "Test Morphology Name",
        "species_id": species_id,
        "strain_id": strain_id,
    }

    public_morph = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=morph_json
        | {
            "name": "public morphology",
            "authorized_public": True,
        },
    )
    assert public_morph.status_code == 200
    public_morph = public_morph.json()

    inaccessible_obj = client.post(
        ROUTE,
        headers=BEARER_TOKEN
        | {
            "virtual-lab-id": "42424242-4242-4000-9000-424242424242",
            "project-id": "42424242-4242-4000-9000-424242424242",
        },
        json=morph_json | {"name": "unaccessable morphology 1"},
    )
    assert inaccessible_obj.status_code == 200
    inaccessible_obj = inaccessible_obj.json()

    private_morph0 = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=morph_json | {"name": "private morphology 0"},
    )
    assert private_morph0.status_code == 200
    private_morph0 = private_morph0.json()

    private_morph1 = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=morph_json
        | {
            "name": "private morphology 1",
        },
    )
    assert private_morph1.status_code == 200
    private_morph1 = private_morph1.json()

    # only return results that matches the desired project, and public ones
    response = client.get(ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS)
    data = response.json()["data"]
    assert len(data) == 3

    ids = {row["id"] for row in data}
    assert ids == {
        public_morph["id"],
        private_morph0["id"],
        private_morph1["id"],
    }

    response = client.get(
        f"{ROUTE}{inaccessible_obj['id']}", headers=BEARER_TOKEN | PROJECT_HEADERS
    )
    assert response.status_code == 404
