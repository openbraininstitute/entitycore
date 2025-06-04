import uuid
from unittest.mock import ANY

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
    assert data["sub_id"] == ANY

    response = client.get(f"{ROUTE}/{id_}")
    assert response.status_code == 200
    data = response.json()
    assert data["given_name"] == "jd"
    assert data["id"] == id_
    assert data["sub_id"] == ANY

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]

    # Two people are expected, the registered one without a subject id
    # and the new agent registered from the token with a subject id
    assert len(data) == 2

    created_from_data, created_from_token = _classify_agents(data)

    assert created_from_data["given_name"] == "jd"
    assert created_from_data["id"] == id_
    assert created_from_data["sub_id"] is None

    assert created_from_token["pref_label"] == "Admin User"
    assert created_from_token["sub_id"] == str(uuid.UUID(int=1))

    # If register again only the data agent added and the token agent is reused
    response = client_admin.post(
        ROUTE,
        json={"given_name": "jd", "family_name": "courcol", "pref_label": "jd courcol"},
    )
    assert response.status_code == 200

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]

    assert len(data) == 3
    assert sum(1 for d in data if d["sub_id"] is not None) == 1


def _classify_agents(data):
    if data[0]["sub_id"] is None:
        return data

    return data[1], data[0]


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422
