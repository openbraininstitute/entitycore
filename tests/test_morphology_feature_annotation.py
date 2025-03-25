import pytest
import sqlalchemy

from .utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    create_reconstruction_morphology_id,
)

ROUTE = "/morphology-feature-annotation"
MORPHOLOGY_ROUTE = "/reconstruction-morphology"


def test_create_annotation(client, species_id, strain_id, brain_region_id):
    reconstruction_morphology_id = create_reconstruction_morphology_id(
        client,
        species_id,
        strain_id,
        brain_region_id,
        authorized_public=False,
    )
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
    response = client.post(ROUTE, json=js)

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

    response = client.get(f"{ROUTE}/{morphology_annotation_id}")

    assert response.status_code == 200, (
        f"Failed to retrieve morphology feature annotation: {response.text}"
    )
    data = response.json()
    morphology_annotation_id = data["id"]
    assert "creation_date" in data
    assert "update_date" in data
    assert "reconstruction_morphology_id" in data
    assert "measurements" in data
    assert len(data["measurements"]) == 2

    response = client.get(f"{MORPHOLOGY_ROUTE}/{reconstruction_morphology_id}")
    assert response.status_code == 200
    assert "morphology_feature_annotation" not in response.json()

    response = client.get(
        f"{MORPHOLOGY_ROUTE}/{reconstruction_morphology_id}",
        params={"expand": "morphology_feature_annotation"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "morphology_feature_annotation" in data
    assert (
        data["morphology_feature_annotation"]["measurements"][0]["measurement_serie"][0]["name"]
        == "Test Measurement Name"
    )

    # Try to create a second annotation
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        response = client.post(
            ROUTE,
            json={
                "reconstruction_morphology_id": reconstruction_morphology_id,
                "measurements": [],
            },
        )


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422


def test_authorization(
    client_admin, client_user, client_no_project, species_id, strain_id, brain_region_id
):
    annotation_js = {
        "measurements": [
            {
                "measurement_of": "Test Measurement Of ID",
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

    reconstruction_morphology_id_public = create_reconstruction_morphology_id(
        client_admin,
        species_id=species_id,
        strain_id=strain_id,
        brain_region_id=brain_region_id,
        authorized_public=True,
    )

    response = client_admin.post(
        ROUTE,
        json=annotation_js | {"reconstruction_morphology_id": reconstruction_morphology_id_public},
    )
    assert response.status_code == 200
    morphology_feature_annotation_id_public = response.json()["id"]

    reconstruction_morphology_id_inaccessible = create_reconstruction_morphology_id(
        client_user,
        species_id=species_id,
        strain_id=strain_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )

    # try to add annotation to inaccessible reconstruction
    response = client_admin.post(
        ROUTE,
        json=annotation_js
        | {"reconstruction_morphology_id": reconstruction_morphology_id_inaccessible},
    )
    assert response.status_code == 404

    # succeed to add annotation to inaccessible reconstruction with a different client
    response = client_user.post(
        ROUTE,
        json=annotation_js
        | {"reconstruction_morphology_id": reconstruction_morphology_id_inaccessible},
    )
    assert response.status_code == 200

    response = client_admin.get(f"{ROUTE}/{response.json()['id']}")
    assert response.status_code == 404

    reconstruction_morphology_id_public_inaccessible = create_reconstruction_morphology_id(
        client_user,
        species_id=species_id,
        strain_id=strain_id,
        brain_region_id=brain_region_id,
        authorized_public=True,
    )
    response = client_admin.post(
        ROUTE,
        json=annotation_js
        | {"reconstruction_morphology_id": reconstruction_morphology_id_public_inaccessible},
    )
    assert response.status_code == 404

    response = client_admin.get(ROUTE)
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1

    # only return public results
    response = client_no_project.get(ROUTE)
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == morphology_feature_annotation_id_public
