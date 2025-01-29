from .utils import PROJECT_HEADERS

def test_create_contribution(client, species_id, strain_id, brain_region_id, license_id):
    response = client.post(
        "/person/",
        json={"givenName": "jd", "familyName": "courcol", "pref_label": "jd courcol"},
    )
    assert response.status_code == 200
    data = response.json()
    person_id = data["id"]

    response = client.post(
        "/role/", json={"name": "important role", "role_id": "important role id"}
    )
    assert response.status_code == 200
    data = response.json()
    role_id = data["id"]

    morph_description = "Test Morphology Description"
    morph_name = "Test Morphology Name"
    response = client.post(
        "/reconstruction_morphology/",
        headers=PROJECT_HEADERS,
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
        "/contribution/",
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
    response = client.get(f"/contribution/{contribution_id}")
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

    response = client.get("/contribution/")
    assert len(response.json()) == 1


def test_missing_contribution(client):
    response = client.get("/contribution/12345")
    assert response.status_code == 404

    response = client.get("/contribution/not_a_contribution_id")
    assert response.status_code == 422
