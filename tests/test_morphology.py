import itertools as it

import pytest
import sqlalchemy


def test_create_reconstruction_morphology(
    client, species_id, strain_id, license_id, brain_region_id
):
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

    response = client.get("/reconstruction_morphology/")
    assert (
        response.status_code == 200
    ), f"Failed to get reconstruction morphologies: {response.text}"


def test_create_annotation(client, species_id, strain_id, brain_region_id):
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

    response = client.get(f"/reconstruction_morphology/{reconstruction_morphology_id}")
    data = response.json()
    assert response.status_code == 200
    assert "morphology_feature_annotation" not in data

    response = client.get(
        f"/reconstruction_morphology/{reconstruction_morphology_id}?expand=morphology_feature_annotation"
    )
    data = response.json()
    assert response.status_code == 200
    assert "morphology_feature_annotation" in data
    assert (
        data["morphology_feature_annotation"]["measurements"][0]["measurement_serie"][0]["name"]
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

    response = client.get("/reconstruction_morphology/?search=test")
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]
    assert facets == {"species": {"Test Species": 1}, "strain": {"Test Strain": 1}}

    assert "data" in data
    data = data["data"]
    assert len(data) == 1


def test_missing_reconstruction_morphology(client):
    response = client.get("/reconstruction_morphology/42424242")
    assert response.status_code == 404

    response = client.get("/reconstruction_morphology/notanumber")
    assert response.status_code == 422


def test_query_reconstruction_morphology(
    client, species_id, strain_id, brain_region_id, license_id
):
    def create_morphologies(nb_morph):
        for i in range(nb_morph):
            morph_description = f"Test Morphology Description {i}"
            morph_name = f"Test Morphology Name {i}"
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

    count = 11
    create_morphologies(count)

    response = client.get("/reconstruction_morphology/")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 10

    response = client.get(
        "/reconstruction_morphology/",
        params={"page_size": 100},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 11

    response = client.get(
        "/reconstruction_morphology/", params={"order_by": "+creation_date", "page_size": 100}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == count
    assert all(
        elem["creation_date"] > prev_elem["creation_date"] for prev_elem, elem in it.pairwise(data)
    )

    response = client.get(
        "/reconstruction_morphology/", params={"order_by": "-creation_date", "page_size": 100}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert all(
        elem["creation_date"] < prev_elem["creation_date"] for prev_elem, elem in it.pairwise(data)
    )

    response = client.get(
        "/reconstruction_morphology/",
        params={"order_by": "+creation_date", "page": 0, "page_size": 3},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 3
    assert [row["id"] for row in data] == [1, 2, 3]

    response = client.get("/reconstruction_morphology/")
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]
    assert facets == {"species": {"Test Species": count}, "strain": {"Test Strain": count}}

    response = client.get("/reconstruction_morphology/?search=Test")
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]
    assert facets == {"species": {"Test Species": count}, "strain": {"Test Strain": count}}
