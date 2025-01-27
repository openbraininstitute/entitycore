def test_create_strain(client):
    response = client.post(
        "/species/", json={"name": "Test Strain", "taxonomy_id": "12345"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Strain"
    assert "id" in data
    species_id = data["id"]
    response = client.post(
        "/strain/",
        json={
            "name": "Test Strain",
            "taxonomy_id": "Taxonomy ID",
            "species_id": species_id,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["taxonomy_id"] == "Taxonomy ID"
    assert data["species_id"] == species_id

    assert "id" in data
