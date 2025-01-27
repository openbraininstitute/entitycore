def test_experimental_neuron_density(client, species_id, strain_id, brain_region_id, license_id):
    neuron_description = "Test neuron Description"
    neuron_name = "Test neuron Name"
    response = client.post(
        "/experimental_neuron_density/",
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": neuron_description,
            "name": neuron_name,
            "brain_location": {"x": 10, "y": 20, "z": 30},
            "legacy_id": "Test Legacy ID",
            "license_id": license_id,
        },
    )
    assert (
        response.status_code == 200
    ), f"Failed to create  experimental neuron density: {response.text}"
    data = response.json()
    print(data)
    assert (
        data["brain_region"]["id"] == brain_region_id
    ), f"Failed to get id for  experimental neuron density: {data}"
    assert (
        data["species"]["id"] == species_id
    ), f"Failed to get species_id for  experimental neuron density: {data}"
    assert (
        data["strain"]["id"] == strain_id
    ), f"Failed to get strain_id for  experimental neuron density: {data}"
    assert (
        data["description"] == neuron_description
    ), f"Failed to get description for  experimental neuron density: {data}"
    assert (
        data["name"] == neuron_name
    ), f"Failed to get name for  experimental neuron density: {data}"
    assert (
        data["license"]["name"] == "Test License"
    ), f"Failed to get license for  experimental neuron density: {data}"

    response = client.get(f"/experimental_neuron_density/{data['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["brain_region"]["id"] == brain_region_id
    assert data["species"]["id"] == species_id
    assert data["strain"]["id"] == strain_id
    assert data["description"] == neuron_description

    response = client.get("/experimental_neuron_density/")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_missing_experimental_neuron_density(client):
    response = client.get("/experimental_neuron_density/42424242")
    assert response.status_code == 404

    response = client.get("/experimental_neuron_density/notanumber")
    assert response.status_code == 422
