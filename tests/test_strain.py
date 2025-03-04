ROUTE = "/strain"


def test_create_strain(client, species_id):
    name = "Test Strain"
    taxonomy_id = "TaxonomyID"
    response = client.post(
        ROUTE,
        json={
            "name": name,
            "taxonomy_id": taxonomy_id,
            "species_id": species_id,
        },
    )
    response.raise_for_status()
    data = response.json()
    assert data["taxonomy_id"] == taxonomy_id
    assert data["species_id"] == species_id
    assert "id" in data
    id_ = data["id"]

    response = client.get(f"{ROUTE}/{id_}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == id_
    assert data["name"] == name
    assert data["taxonomy_id"] == taxonomy_id

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == name
    assert data[0]["id"] == id_


def test_missing_role(client):
    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422
