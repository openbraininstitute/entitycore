from app.db.model import Agent, Organization

from tests.utils import MISSING_ID, MISSING_ID_COMPACT, assert_request, count_db_class

ROUTE = "/organization"


def test_create_organization(client, client_admin):
    label = "test_organization label"
    alternative_name = "test organization alternative name"
    response = client_admin.post(
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


def test_delete_one(db, client, client_admin):
    response = client_admin.post(
        ROUTE,
        json={"pref_label": "foo", "alternative_name": "bar"},
    )
    assert response.status_code == 200
    data = response.json()

    model_id = data["id"]

    assert count_db_class(db, Organization) == 1

    # 1 created_by/updated_by 1 Organization
    assert count_db_class(db, Agent) == 2

    data = assert_request(client.delete, url=f"{ROUTE}/{model_id}", expected_status_code=403).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    data = assert_request(client_admin.delete, url=f"{ROUTE}/{model_id}").json()
    assert data["id"] == str(model_id)

    assert count_db_class(db, Organization) == 0
    assert count_db_class(db, Agent) == 1


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422
