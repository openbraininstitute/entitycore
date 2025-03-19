import pytest

from .utils import MISSING_ID, MISSING_ID_COMPACT, PROJECT_HEADERS

ROUTE = "/experimental-neuron-density"


@pytest.mark.usefixtures("skip_project_check")
def test_experimental_neuron_density(client, species_id, strain_id, brain_region_id, license_id):
    neuron_description = "Test neuron Description"
    neuron_name = "Test neuron Name"
    response = client.post(
        ROUTE,
        headers=PROJECT_HEADERS,
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": neuron_description,
            "name": neuron_name,
            "legacy_id": "Test Legacy ID",
            "license_id": license_id,
        },
    )
    assert response.status_code == 200, (
        f"Failed to create experimental neuron density: {response.text}"
    )
    data = response.json()
    assert data["brain_region"]["id"] == brain_region_id, (
        f"Failed to get id for  experimental neuron density: {data}"
    )
    assert data["species"]["id"] == species_id, (
        f"Failed to get species_id for  experimental neuron density: {data}"
    )
    assert data["strain"]["id"] == strain_id, (
        f"Failed to get strain_id for  experimental neuron density: {data}"
    )
    assert data["description"] == neuron_description, (
        f"Failed to get description for  experimental neuron density: {data}"
    )
    assert data["name"] == neuron_name, (
        f"Failed to get name for  experimental neuron density: {data}"
    )
    assert data["license"]["name"] == "Test License", (
        f"Failed to get license for  experimental neuron density: {data}"
    )

    response = client.get(
        f"{ROUTE}/{data['id']}",
        headers=PROJECT_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["brain_region"]["id"] == brain_region_id
    assert data["species"]["id"] == species_id
    assert data["strain"]["id"] == strain_id
    assert data["description"] == neuron_description

    response = client.get(ROUTE, headers=PROJECT_HEADERS)
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


@pytest.mark.usefixtures("skip_project_check")
def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422


@pytest.mark.usefixtures("skip_project_check")
def test_authorization(client, species_id, strain_id, license_id, brain_region_id):
    js = {
        "brain_region_id": brain_region_id,
        "species_id": species_id,
        "strain_id": strain_id,
        "description": "the finest description",
        "legacy_id": "Test Legacy ID",
        "license_id": license_id,
    }

    public_obj = client.post(
        ROUTE,
        headers=PROJECT_HEADERS,
        json=js
        | {
            "name": "public obj",
            "authorized_public": True,
        },
    )
    assert public_obj.status_code == 200
    public_obj = public_obj.json()

    inaccessible_obj = client.post(
        ROUTE,
        headers={
            "virtual-lab-id": "42424242-4242-4000-9000-424242424242",
            "project-id": "42424242-4242-4000-9000-424242424242",
        },
        json=js
        | {
            "name": "unaccessable obj",
        },
    )
    assert inaccessible_obj.status_code == 200
    inaccessible_obj = inaccessible_obj.json()

    private_obj0 = client.post(ROUTE, headers=PROJECT_HEADERS, json=js | {"name": "private obj 0"})
    assert private_obj0.status_code == 200
    private_obj0 = private_obj0.json()

    private_obj1 = client.post(
        ROUTE,
        headers=PROJECT_HEADERS,
        json=js
        | {
            "name": "private obj 1",
        },
    )
    assert private_obj1.status_code == 200
    private_obj1 = private_obj1.json()

    # only return results that matches the desired project, and public ones
    response = client.get(ROUTE, headers=PROJECT_HEADERS)
    data = response.json()["data"]
    assert len(data) == 3

    ids = {row["id"] for row in data}
    assert ids == {
        public_obj["id"],
        private_obj0["id"],
        private_obj1["id"],
    }

    response = client.get(f"{ROUTE}/{inaccessible_obj['id']}", headers=PROJECT_HEADERS)
    assert response.status_code == 404
