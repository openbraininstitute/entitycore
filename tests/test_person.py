from tests.utils import MISSING_ID, MISSING_ID_COMPACT

ROUTE = "/person"


def test_create_person(client):
    response = client.post(
        ROUTE,
        json={"givenName": "jd", "familyName": "courcol", "pref_label": "jd courcol"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["givenName"] == "jd"
    assert data["familyName"] == "courcol"
    assert "id" in data
    id_ = data["id"]

    response = client.get(f"{ROUTE}/{id_}")
    assert response.status_code == 200
    data = response.json()
    assert data["givenName"] == "jd"
    assert data["id"] == id_

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data[0]["givenName"] == "jd"
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
