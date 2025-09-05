from app.db.model import License

from tests.utils import MISSING_ID, MISSING_ID_COMPACT, assert_request, count_db_class

ROUTE = "/license"
ADMIN_ROUTE = "/admin/license"


def test_create_license(client, client_admin):
    response = client_admin.post(
        ROUTE,
        json={
            "name": "Test License",
            "description": "a license description",
            "label": "a label",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test License"
    assert "id" in data
    assert data["description"] == "a license description"
    id_ = data["id"]

    response = client.get(f"{ROUTE}/{id_}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test License"
    assert data["description"] == "a license description"

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "Test License"
    assert data[0]["description"] == "a license description"


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422


def test_delete_one(db, client, client_admin):
    response = client_admin.post(
        ROUTE,
        json={
            "name": "Test License",
            "description": "a license description",
            "label": "a label",
        },
    )
    assert response.status_code == 200
    model_id = response.json()["id"]

    assert count_db_class(db, License) == 1

    data = assert_request(
        client.delete, url=f"{ADMIN_ROUTE}/{model_id}", expected_status_code=403
    ).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    data = assert_request(client_admin.delete, url=f"{ADMIN_ROUTE}/{model_id}").json()
    assert data["id"] == str(model_id)

    assert count_db_class(db, License) == 0
