
import pytest
import sqlalchemy



def test_experimental_neuron_density(client):
    response = client.post(
        "/species/", json={"name": "Test Species", "taxonomy_id": "12345"}
    )
    assert response.status_code == 200, f"Failed to create species: {response.text}"
    data = response.json()
    assert data["name"] == "Test Species"
    assert "id" in data, f"Failed to get id for species: {data}"
    species_id = data["id"]
    response = client.post(
        "/strain/",
        json={
            "name": "Test Strain",
            "taxonomy_id": "Taxonomy ID",
            "species_id": species_id,
        },
    )
    assert response.status_code == 200, f"Failed to create strain: {response.text}"
    data = response.json()
    assert data["taxonomy_id"] == "Taxonomy ID"
    assert "id" in data, f"Failed to get id for strain: {data}"
    strain_id = data["id"]
    ontology_id = "Test Ontology ID"
    response = client.post(
        "/brain_region/", json={"name": "Test Brain Region", "ontology_id": ontology_id}
    )
    assert (
        response.status_code == 200
    ), f"Failed to create brain region: {response.text}"
    data = response.json()
    assert data["name"] == "Test Brain Region"
    assert data["ontology_id"] == ontology_id
    assert "id" in data, f"Failed to get id for brain region: {data}"
    brain_region_id = data["id"]
    response = client.post(
        "/license/",
        json={"name": "Test License", "description": "a license description"},
    )
    assert response.status_code == 200
    data = response.json()
    license_id = data["id"]
    assert "id" in data, f"Failed to get id for license: {data}"
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

    response=client.get(f"/experimental_neuron_density/{data['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["brain_region"]["id"] == brain_region_id
    assert data["species"]["id"] == species_id
    assert data["strain"]["id"] == strain_id
    assert data["description"] == neuron_description