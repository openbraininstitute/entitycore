from .utils import MISSING_ID, MISSING_ID_COMPACT

ROUTE = "/experimental-bouton-density"


def test_experimental_bouton_density(client, species_id, strain_id, license_id, brain_region_id):
    bouton_description = "Test bouton Description"
    bouton_name = "Test bouton Name"
    response = client.post(
        ROUTE,
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
    assert response.status_code == 200, (
        f"Failed to create  experimental bouton density: {response.text}"
    )
    data = response.json()
    assert data["brain_region"]["id"] == brain_region_id, (
        f"Failed to get id for  experimental bouton density: {data}"
    )
    assert data["species"]["id"] == species_id, (
        f"Failed to get species_id for  experimental bouton density: {data}"
    )
    assert data["strain"]["id"] == strain_id, (
        f"Failed to get strain_id for  experimental bouton density: {data}"
    )
    assert data["description"] == bouton_description, (
        f"Failed to get description for  experimental bouton density: {data}"
    )
    assert data["name"] == bouton_name, (
        f"Failed to get name for  experimental bouton density: {data}"
    )
    assert data["license"]["name"] == "Test License", (
        f"Failed to get license for  experimental bouton density: {data}"
    )

    response = client.get(f"{ROUTE}/{data['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["brain_region"]["id"] == brain_region_id
    assert data["species"]["id"] == species_id
    assert data["strain"]["id"] == strain_id
    assert data["description"] == bouton_description

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422


def test_authorization(client_1, client_2, species_id, strain_id, license_id, brain_region_id):
    js = {
        "brain_region_id": brain_region_id,
        "description": "a great description",
        "legacy_id": "Test Legacy ID",
        "license_id": str(license_id),
        "species_id": str(species_id),
        "strain_id": str(strain_id),
    }

    public_obj = client_1.post(
        ROUTE,
        json=js
        | {
            "name": "public obj",
            "authorized_public": True,
        },
    )
    assert public_obj.status_code == 200
    public_obj = public_obj.json()

    inaccessible_obj = client_2.post(ROUTE, json=js | {"name": "inaccessible obj"})
    assert inaccessible_obj.status_code == 200
    inaccessible_obj = inaccessible_obj.json()

    private_obj0 = client_1.post(ROUTE, json=js | {"name": "private obj 0"})
    assert private_obj0.status_code == 200
    private_obj0 = private_obj0.json()

    private_obj1 = client_1.post(ROUTE, json=js | {"name": "private obj 1"})
    assert private_obj1.status_code == 200
    private_obj1 = private_obj1.json()

    # only return results that matches the desired project, and public ones
    response = client_1.get(ROUTE)
    data = response.json()["data"]
    assert len(data) == 3

    ids = {row["id"] for row in data}
    assert ids == {
        public_obj["id"],
        private_obj0["id"],
        private_obj1["id"],
    }

    response = client_1.get(f"{ROUTE}/{inaccessible_obj['id']}")
    assert response.status_code == 404
