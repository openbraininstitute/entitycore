def create_reconstruction_morphology_id(
    client, species_id, strain_id, brain_region_id, headers, authorized_public,
    name="Test Morphology Name",
    description="Test Morphology Description",
):
    response = client.post(
        "/reconstruction_morphology/",
        headers=headers,
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": description,
            "name": name,
            "brain_location": {"x": 10, "y": 20, "z": 30},
            "legacy_id": "Test Legacy ID",
            "authorized_public": authorized_public,
        },
    )
    assert response.status_code == 200
    return response.json()["id"]
