
def test_create_species(client):
    response = client.post(
        "/species/", json={"name": "Test Species", "taxonomy_id": "12345"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Species"
    assert data["taxonomy_id"] == "12345"
    assert "id" in data