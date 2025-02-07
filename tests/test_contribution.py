import pytest

from .utils import BEARER_TOKEN, PROJECT_HEADERS, skip_project_check

ROUTE = "/contribution/"

@pytest.mark.usefixtures("skip_project_check")
def test_create_contribution(
    client, person_id, role_id, species_id, strain_id, brain_region_id, license_id
):
    morph_description = "Test Morphology Description"
    morph_name = "Test Morphology Name"

    with skip_project_check():
        response = client.post(
            "/reconstruction_morphology/",
            headers=BEARER_TOKEN|PROJECT_HEADERS,
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

    assert response.status_code == 200
    data = response.json()
    entity_id = data["id"]
    assert entity_id is not None
    response = client.post(
        ROUTE,
        headers=BEARER_TOKEN|PROJECT_HEADERS,
        json={
            "agent_id": person_id,
            "role_id": role_id,
            "entity_id": entity_id,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["agent"]["id"] == person_id
    assert data["agent"]["givenName"] == "jd"
    assert data["agent"]["familyName"] == "courcol"
    assert data["role"]["id"] == role_id
    assert data["role"]["name"] == "important role"
    assert data["role"]["role_id"] == "important role id"
    assert data["entity"]["id"] == entity_id
    assert data["entity"]["name"] == morph_name
    assert data["entity"]["description"] == morph_description
    assert data["creation_date"] is not None
    assert data["update_date"] is not None

    contribution_id = data["id"]
    response = client.get(
        f"{ROUTE}{contribution_id}", headers=BEARER_TOKEN | PROJECT_HEADERS
    )
    assert response.status_code == 200
    data = response.json()
    assert data["agent"]["id"] == person_id
    assert data["agent"]["givenName"] == "jd"
    assert data["agent"]["familyName"] == "courcol"
    assert data["role"]["id"] == role_id
    assert data["role"]["name"] == "important role"
    assert data["role"]["role_id"] == "important role id"
    assert data["entity"]["id"] == entity_id
    assert data["entity"]["name"] == morph_name
    assert data["entity"]["description"] == morph_description
    assert data["creation_date"] is not None
    assert data["update_date"] is not None
    assert data["id"] == contribution_id

    response = client.get(ROUTE, headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert len(response.json()) == 1


@pytest.mark.usefixtures("skip_project_check")
def test_missing(client):
    response = client.get(ROUTE + "12345", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 404

    response = client.get(ROUTE + "not_a_contribution_id",
                          headers=BEARER_TOKEN | PROJECT_HEADERS
    )
    assert response.status_code == 422


@pytest.mark.usefixtures("skip_project_check")
def test_authorization(client):
    response = client.get(ROUTE + "12345", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 404

    response = client.get(ROUTE + "not_a_contribution_id",
                          headers=BEARER_TOKEN | PROJECT_HEADERS
    )
    assert response.status_code == 422
