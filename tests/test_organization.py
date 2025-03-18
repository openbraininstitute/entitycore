from tests.utils import MISSING_ID, MISSING_ID_COMPACT

ROUTE = "/organization"


def test_create_organization(client):
    label = "test_organization label"
    alternative_name = "test organization alternative name"
    response = client.post(
        ROUTE,
        json={"pref_label": label, "alternative_name": alternative_name},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pref_label"] == label
    assert data["alternative_name"] == alternative_name
    assert "id" in data
    id_ = data["id"]

    response = client.get(f"{ROUTE}/{id_}")
    assert response.status_code == 200
    data = response.json()
    assert data["pref_label"] == label
    assert data["alternative_name"] == alternative_name
    assert data["id"] == id_

    response = client.get(ROUTE)
    assert response.status_code == 200

    data = response.json()["data"]
    assert data[0]["id"] == id_
    assert len(data) == 1


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422
