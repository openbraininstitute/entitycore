def test_create_contribution(client):
    response = client.post("/person/", json={"givenName": "jd", "familyName": "courcol"})
    assert response.status_code == 200
    data = response.json()
    person_id = data["id"]

    response = client.post(
        "/role/", json={"name": "important role", "role_id": "important role id"}
    )
    assert response.status_code == 200
    data = response.json()
    role_id = data["id"]

    response = client.post("/species/", json={"name": "Test Species", "taxonomy_id": "12345"})
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
    assert response.status_code == 200, f"Failed to create brain region: {response.text}"
    data = response.json()
    brain_region_id = data["id"]
    response = client.post(
        "/license/",
        json={
            "name": "Test License",
            "description": "a license description",
            "label": "Test License Label",
        },
    )
    assert response.status_code == 200
    data = response.json()
    license_id = data["id"]
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
