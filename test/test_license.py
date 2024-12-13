import pytest
import sqlalchemy


def test_create_license(client):
    response = client.post(
        "/license/",
        json={"name": "Test License", "description": "a license description", "label": "a label"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test License"
    assert "id" in data
    assert data["description"] == "a license description"
    id_ = data["id"]
    response = client.get("/license/{}".format(id_))
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test License"
    assert data["description"] == "a license description"
    response = client.get("/license/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test License"
    assert data[0]["description"] == "a license description"
