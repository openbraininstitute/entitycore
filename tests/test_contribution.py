ROUTE = "/contribution/"


def test_create_contribution(
    client, person_id, role_id, species_id, strain_id, brain_region_id, license_id
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
    response.raise_for_status()
    data = response.json()
    entity_id = data["id"]
    assert entity_id is not None

    response = client.post(
        ROUTE,
        json={
            "agent_id": person_id,
            "role_id": role_id,
            "entity_id": entity_id,
        },
    )
    response.raise_for_status()
    data = response.json()
    assert data["agent"]["id"] == person_id
    assert data["agent"]["givenName"] == "jd"
    assert data["agent"]["familyName"] == "courcol"
    assert data["role"]["id"] == role_id
    assert data["role"]["name"] == "important role"
    assert data["role"]["role_id"] == "important role id"
    assert data["entity"]["id"] == entity_id

    contribution_id = data["id"]
    response = client.get(f"{ROUTE}{contribution_id}")
    response.raise_for_status()
    data = response.json()
    assert data["agent"]["id"] == person_id
    assert data["agent"]["givenName"] == "jd"
    assert data["agent"]["familyName"] == "courcol"
    assert data["role"]["id"] == role_id
    assert data["role"]["name"] == "important role"
    assert data["role"]["role_id"] == "important role id"
    assert data["entity"]["id"] == entity_id
    assert data["id"] == contribution_id

    response = client.get("/contribution/")
    assert len(response.json()) == 1

    response = client.get(f"/reconstruction_morphology/{entity_id}")
    response.raise_for_status()
    data = response.json()
    assert "contributors" in data
    assert len(data["contributors"]) == 1

    response = client.get("/reconstruction_morphology/")
    response.raise_for_status()
    data = response.json()["data"]
    assert len(data) == 1
    assert len(data[0]["contributors"]) == 1


def test_missing_contribution(client):
    response = client.get(ROUTE + "12345")
    assert response.status_code == 404

    response = client.get(ROUTE + "not_a_contribution_id")
    assert response.status_code == 422
