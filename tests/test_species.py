from .utils import check_creation_fields
from tests.utils import MISSING_ID, MISSING_ID_COMPACT

ROUTE = "/species"


def test_create_species(client, client_admin):
    count = 3
    items = []
    for i in range(count):
        name = f"Test Species {i}"
        taxonomy_id = f"12345_{i}"
        response = client_admin.post(ROUTE, json={"name": name, "taxonomy_id": taxonomy_id})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name
        assert data["taxonomy_id"] == taxonomy_id
        check_creation_fields(data)
        assert "id" in data
        items.append(data)

    response = client.get(f"{ROUTE}/{items[0]['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data == items[0]
    check_creation_fields(data)

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == count
    assert data == items
    check_creation_fields(data[0])

    # test filter
    response = client.get(ROUTE, params={"name": "Test Species 1"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data == [items[1]]
    check_creation_fields(data[0])


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422
