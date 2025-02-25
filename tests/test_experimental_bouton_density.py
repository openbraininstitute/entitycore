import pytest

from .utils import PROJECT_HEADERS

ROUTE = "/experimental_bouton_density/"


@pytest.mark.usefixtures("skip_project_check")
def test_experimental_bouton_density(client, species_id, strain_id, license_id, brain_region_id):
    bouton_description = "Test bouton Description"
    bouton_name = "Test bouton Name"
    response = client.post(
        ROUTE,
        headers=PROJECT_HEADERS,
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": bouton_description,
            "name": bouton_name,
            "legacy_id": "Test Legacy ID",
            "license_id": license_id,
        },
    )
    assert (
        response.status_code == 200
    ), f"Failed to create  experimental bouton density: {response.text}"
    data = response.json()
    assert (
        data["brain_region"]["id"] == brain_region_id
    ), f"Failed to get id for  experimental bouton density: {data}"
    assert (
        data["species"]["id"] == species_id
    ), f"Failed to get species_id for  experimental bouton density: {data}"
    assert (
        data["strain"]["id"] == strain_id
    ), f"Failed to get strain_id for  experimental bouton density: {data}"
    assert (
        data["description"] == bouton_description
    ), f"Failed to get description for  experimental bouton density: {data}"
    assert (
        data["name"] == bouton_name
    ), f"Failed to get name for  experimental bouton density: {data}"
    assert (
        data["license"]["name"] == "Test License"
    ), f"Failed to get license for  experimental bouton density: {data}"

    response = client.get(ROUTE + str(data["id"]), headers=PROJECT_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["brain_region"]["id"] == brain_region_id
    assert data["species"]["id"] == species_id
    assert data["strain"]["id"] == strain_id
    assert data["description"] == bouton_description

    response = client.get(ROUTE, headers=PROJECT_HEADERS)
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.usefixtures("skip_project_check")
def test_missing_bouton_density(client):
    response = client.get(ROUTE + "42424242", headers=PROJECT_HEADERS)
    assert response.status_code == 404

    response = client.get(ROUTE + "notanumber", headers=PROJECT_HEADERS)
    assert response.status_code == 422


@pytest.mark.usefixtures("skip_project_check")
def test_authorization(client, species_id, strain_id, license_id, brain_region_id):
    js = {
        "brain_region_id": brain_region_id,
        "description": "a great description",
        "legacy_id": "Test Legacy ID",
        "license_id": license_id,
        "species_id": species_id,
        "strain_id": strain_id,
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
        json=js | {"name": "unaccessable obj"},
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
    data = response.json()
    assert len(data) == 3

    ids = {row["id"] for row in data}
    assert ids == {
        public_obj["id"],
        private_obj0["id"],
        private_obj1["id"],
    }

    response = client.get(f"{ROUTE}{inaccessible_obj['id']}", headers=PROJECT_HEADERS)
    assert response.status_code == 404
