import pytest
import sqlalchemy

from .utils import BEARER_TOKEN, PROJECT_HEADERS

ROUTE = "/morphology_feature_annotation/"
MORPHOLOGY_ROUTE = "/reconstruction_morphology/"


@pytest.fixture
def reconstruction_morphology_id(client, species_id, strain_id, brain_region_id):
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
    return response.json()["id"]


@pytest.mark.usefixtures("skip_project_check")
def test_create_annotation(client, reconstruction_morphology_id):
    measurement_of = "Test Measurement Of ID"
    js = {
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
        }
    response = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json=js,
    )

    assert response.status_code == 200, (
        f"Failed to create morphology feature annotation: {response.text}"
    )
    data = response.json()
    morphology_annotation_id = data["id"]
    assert "creation_date" in data
    assert "update_date" in data
    assert "reconstruction_morphology_id" in data
    assert "measurements" in data
    assert len(data["measurements"]) == 2

    response = client.get(f"{ROUTE}{morphology_annotation_id}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
                          )
    data = response.json()
    morphology_annotation_id = data["id"]
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

    # Try and create a second annotation
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        response = client.post(
            ROUTE,
            headers=BEARER_TOKEN | PROJECT_HEADERS,
            json={
                "reconstruction_morphology_id": reconstruction_morphology_id,
                "measurements": [],
            },
        )

@pytest.mark.usefixtures("skip_project_check")
def test_missing(client):
    response = client.get(ROUTE + "42424242", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 404

    response = client.get(ROUTE + "notanumber", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 422


@pytest.mark.usefixtures("skip_project_check")
def test_authorization(client, reconstruction_morphology_id):
    pass
