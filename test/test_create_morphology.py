import pytest
import sqlalchemy


def test_create_species(client):
    response = client.post(
        "/species/", json={"name": "Test Species", "taxonomy_id": "12345"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Species"
    assert "id" in data


def test_create_strain(client):
    response = client.post(
        "/species/", json={"name": "Test Strain", "taxonomy_id": "12345"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Strain"
    assert "id" in data
    response = client.post(
        "/strain/",
        json={
            "name": "Test Strain",
            "taxonomy_id": "Taxonomy ID",
            "species_id": data["id"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["taxonomy_id"] == "Taxonomy ID"
    assert "id" in data


def test_create_reconstruction_morphology(client):
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
    morph_description = "Test Morphology Description"
    morph_name = "Test Morphology Name"
    response = client.post(
        "/reconstruction_morphology/",
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
    print(data)
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
    assert (
        data["name"] == morph_name
    ), f"Failed to get name for reconstruction morphology: {data}"
    assert (
        data["license"]["name"] == "Test License"
    ), f"Failed to get license for reconstruction morphology: {data}"


def test_create_annotation(client):
    response = client.post(
        "/species/", json={"name": "Test Species", "taxonomy_id": "12345"}
    )
    assert response.status_code == 200, f"Failed to create species: {response.text}"
    data = response.json()
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
    strain_id = data["id"]
    ontology_id = "Test Ontology ID"
    response = client.post(
        "/brain_region/", json={"name": "Test Brain Region", "ontology_id": ontology_id}
    )
    assert (
        response.status_code == 200
    ), f"Failed to create brain region: {response.text}"
    data = response.json()
    assert "id" in data, f"Failed to get id for brain region: {data}"
    brain_region_id = data["id"]
    morph_description = "Test Morphology Description"
    morph_name = "Test Morphology Name"
    response = client.post(
        "/reconstruction_morphology/",
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": morph_description,
            "name": morph_name,
            "brain_location": {"x": 10, "y": 20, "z": 30},
            "legacy_id": "Test Legacy ID",
        },
    )
    assert (
        response.status_code == 200
    ), f"Failed to create reconstruction morphology: {response.text}"
    data = response.json()
    reconstruction_morphology_id = data["id"]
    measurement_of = "Test Measurement Of ID"
    response = client.post(
        "/morphology_feature_annotation/",
        json={
            "reconstruction_morphology_id": reconstruction_morphology_id,
            "measurements": [
                {
                    "measurement_of": measurement_of,
                    "measurement_serie": [
                        {
                            "name": "Test Measurement Name",
                            "value": 10,
                        },
                        {
                            "name": "Test Measurement Name 2",
                            "value": 20,
                        },
                    ],
                },
                {
                    "measurement_of": measurement_of + " 2",
                    "measurement_serie": [
                        {
                            "name": "Test Measurement Name",
                            "value": 10,
                        },
                        {
                            "name": "Test Measurement Name 2",
                            "value": 20,
                        },
                    ],
                },
            ],
        },
    )

    assert (
        response.status_code == 200
    ), f"Failed to create morphology feature annotation: {response.text}"
    data = response.json()
    assert "id" in data, f"Failed to get id for morphology feature annotation: {data}"
    assert (
        "creation_date" in data
    ), f"Failed to get creation_date for morphology feature annotation: {data}"
    assert (
        "update_date" in data
    ), f"Failed to get update_date for morphology feature annotation: {data}"
    assert (
        "reconstruction_morphology_id" in data
    ), f"Failed to get reconstruction_morphology_id for morphology feature annotation: {data}"
    assert (
        "measurements" in data
    ), f"Failed to get measurements for morphology feature annotation: {data}"
    assert (
        len(data["measurements"]) == 2
    ), f"Failed to get correct number of measurements for morphology feature annotation: {data}"

    response = client.get(
        "/reconstruction_morphology/{}".format(reconstruction_morphology_id)
    )
    data = response.json()
    assert response.status_code == 200
    assert "morphology_feature_annotation" not in data

    response = client.get(
        "/reconstruction_morphology/{}?expand=morphology_feature_annotation".format(
            reconstruction_morphology_id
        )
    )
    data = response.json()
    assert response.status_code == 200
    assert "morphology_feature_annotation" in data
    assert (
        data["morphology_feature_annotation"]["measurements"][0]["measurement_serie"][
            0
        ]["name"]
        == "Test Measurement Name"
    )
    with pytest.raises(sqlalchemy.exc.IntegrityError):

        response = client.post(
            "/morphology_feature_annotation/",
            json={
                "reconstruction_morphology_id": reconstruction_morphology_id,
                "measurements": [
                    {
                        "measurement_of": measurement_of,
                        "measurement_serie": [
                            {
                                "name": "Test Measurement Name second time",
                                "value": 100,
                            },
                            {
                                "name": "Test Measurement Name 2",
                                "value": 200,
                            },
                        ],
                    },
                    {
                        "measurement_of": measurement_of + " 2",
                        "measurement_serie": [
                            {
                                "name": "Test Measurement Name second time",
                                "value": 100,
                            },
                            {
                                "name": "Test Measurement Name 2",
                                "value": 200,
                            },
                        ],
                    },
                ],
            },
        )
