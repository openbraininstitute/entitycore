def test_experimental_bouton_density(client, species_id, strain_id, license_id, brain_region_id):
    bouton_description = "Test bouton Description"
    bouton_name = "Test bouton Name"
    response = client.post(
        "/experimental_bouton_density/",
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": bouton_description,
            "name": bouton_name,
            "brain_location": {"x": 10, "y": 20, "z": 30},
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

    response = client.get(f"/experimental_bouton_density/{data['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["brain_region"]["id"] == brain_region_id
    assert data["species"]["id"] == species_id
    assert data["strain"]["id"] == strain_id
    assert data["description"] == bouton_description
    assert data["brain_location"] == {"x": 10.0, "y": 20.0, "z": 30.0}

    response = client.get("/experimental_bouton_density/")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_missing_bouton_density(client):
    response = client.get("/experimental_bouton_density/42424242")
    assert response.status_code == 404

    response = client.get("/experimental_bouton_density/notanumber")
    assert response.status_code == 422
