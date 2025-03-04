ROUTE = "/strain"


def test_create_strain(client, species_id):
    count = 3
    items = []
    for i in range(count):
        name = f"Test Strain {i}"
        taxonomy_id = f"TaxonomyID_{i}"
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
        items.append(data)

    response = client.get(f"{ROUTE}/{items[0]['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data == items[0]

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == count
    assert data == items

    # test filter
    response = client.get(f"{ROUTE}", params={"name": "Test Strain 1"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data == [items[1]]


def test_missing_role(client):
    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422
