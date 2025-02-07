import pytest

from .utils import BEARER_TOKEN, PROJECT_HEADERS, UNRELATED_PROJECT_HEADERS

ROUTE = "/contribution/"


@pytest.mark.usefixtures("skip_project_check")
def test_create_contribution(
    client, person_id, role_id, species_id, strain_id, brain_region_id, license_id
):
    morph_description = "Test Morphology Description"
    morph_name = "Test Morphology Name"

    response = client.post(
        "/reconstruction_morphology/",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
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
        headers=BEARER_TOKEN | PROJECT_HEADERS,
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
    response = client.get(f"{ROUTE}{contribution_id}", headers=BEARER_TOKEN | PROJECT_HEADERS)
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

    response = client.get(ROUTE + "not_a_contribution_id", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 422


@pytest.mark.usefixtures("skip_project_check")
def test_authorization(
    client, brain_region_id, species_id, strain_id, license_id, person_id, role_id
):
    response = client.post(
        "/reconstruction_morphology/",
        headers=BEARER_TOKEN | UNRELATED_PROJECT_HEADERS,
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": "Test Morphology Description",
            "name": "Test Morphology Name",
            "brain_location": {"x": 10, "y": 20, "z": 30},
            "legacy_id": "Test Legacy ID",
            "license_id": license_id,
        },
    )

    inaccessible_entity_id = response.json()["id"]
    response = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "agent_id": person_id,
            "role_id": role_id,
            "entity_id": inaccessible_entity_id,
        },
    )
    # can't attach contributions to projects unrelated to us
    assert response.status_code == 404

    response = client.post(
        "/reconstruction_morphology/",
        headers=BEARER_TOKEN | UNRELATED_PROJECT_HEADERS,
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": "Public Object",
            "name": "Test Morphology Name",
            "brain_location": {"x": 10, "y": 20, "z": 30},
            "legacy_id": "Public Object",
            "license_id": license_id,
            "authorized_public": True
        },
    )
    public_entity_id = response.json()["id"]

    response = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "agent_id": person_id,
            "role_id": role_id,
            "entity_id": public_entity_id
        },
    )
    # can't attach contributions to projects unrelated to us, even if public
    assert response.status_code == 404

    public_obj = client.post(
        ROUTE,
        headers=BEARER_TOKEN | UNRELATED_PROJECT_HEADERS,
        json={
            "agent_id": person_id,
            "role_id": role_id,
            "entity_id": public_entity_id,
        },
    )
    assert public_obj.status_code == 200
    public_obj = public_obj.json()

    response = client.get(f"{ROUTE}{public_obj['id']}",
                          headers=BEARER_TOKEN | PROJECT_HEADERS,
                          )
    # can get the contributor if the entity is public
    assert response.status_code == 200

    response = client.get(f"{ROUTE}",
                          headers=BEARER_TOKEN | PROJECT_HEADERS,
                          )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1  # only public entity is available
    assert data[0]["id"] == public_obj["id"]
    assert data[0]["entity"]["id"] == public_entity_id
    assert data[0]["entity"]["authorized_public"]
