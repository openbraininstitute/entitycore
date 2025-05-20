from tests.utils import MISSING_ID, MISSING_ID_COMPACT

ROUTE = "/person"


def test_create_person(client, client_admin):
    response = client_admin.post(
        ROUTE,
        json={"given_name": "jd", "family_name": "courcol", "pref_label": "jd courcol"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["given_name"] == "jd"
    assert data["family_name"] == "courcol"
    assert "id" in data
    id_ = data["id"]

    response = client.get(f"{ROUTE}/{id_}")
    assert response.status_code == 200
    data = response.json()
    assert data["given_name"] == "jd"
    assert data["id"] == id_

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data[0]["given_name"] == "jd"
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
