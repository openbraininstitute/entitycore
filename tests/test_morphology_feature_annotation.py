import pytest
import sqlalchemy

from .utils import BEARER_TOKEN, PROJECT_HEADERS

ROUTE = "/morphology_feature_annotation/"
MORPHOLOGY_ROUTE = "/reconstruction_morphology/"


@pytest.mark.usefixtures("skip_project_check")
def test_create_annotation(client, species_id, strain_id, brain_region_id):
    response = client.post(
        MORPHOLOGY_ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": "Test Morphology Description",
            "name": "Test Morphology Name",
            "brain_location": {"x": 10, "y": 20, "z": 30},
            "legacy_id": "Test Legacy ID",
        },
    )
    assert response.status_code == 200
    reconstruction_morphology_id = response.json()["id"]

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

    assert response.status_code == 200, (
        f"Failed to create morphology feature annotation: {response.text}"
    )
    data = response.json()
    assert "id" in data
    assert "creation_date" in data
    assert "update_date" in data
    assert "reconstruction_morphology_id" in data
    assert "measurements" in data
    assert len(data["measurements"]) == 2

    response = client.get(
        f"{MORPHOLOGY_ROUTE}{reconstruction_morphology_id}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert response.status_code == 200
    assert "morphology_feature_annotation" not in response.json()

    response = client.get(
        f"{MORPHOLOGY_ROUTE}{reconstruction_morphology_id}?expand=morphology_feature_annotation",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
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

    response = client.get(
        "/reconstruction_morphology/?search=test", headers=BEARER_TOKEN | PROJECT_HEADERS
    )
    assert response.status_code == 200
    data = response.json()

    assert "facets" in data
    facets = data["facets"]
    assert facets == {"species": {"Test Species": 1}, "strain": {"Test Strain": 1}}

    assert "data" in data
    data = data["data"]
    assert len(data) == 1


@pytest.mark.usefixtures("skip_project_check")
def test_authorization(client, species_id, strain_id, brain_region_id):
    response = client.post(
        MORPHOLOGY_ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": "Test Morphology Description",
            "name": "Test Morphology Name",
            "brain_location": {"x": 10, "y": 20, "z": 30},
            "legacy_id": "Test Legacy ID",
        },
    )
    assert response.status_code == 200
    reconstruction_morphology_id = response.json()["id"]
    assert False
