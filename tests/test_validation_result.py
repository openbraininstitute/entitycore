import uuid

from fastapi.testclient import TestClient

ROUTE = "/validation-result"


def test_get_validation_result(client: TestClient, validation_result_id):
    response = client.get(f"{ROUTE}/{validation_result_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == validation_result_id
    assert "passed" in data
    assert "validated_entity_id" in data
    assert "creation_date" in data
    assert "update_date" in data


def test_missing(client):
    response = client.get(f"{ROUTE}/{uuid.uuid4()}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/notauuid")
    assert response.status_code == 422


def test_create_validation_result(client: TestClient, morphology_id):
    response = client.post(
        ROUTE,
        json={
            "name": "test_validation",
            "passed": True,
            "validated_entity_id": morphology_id,
        },
    )
    # should return 201 Created, but fastapi default is 200 OK
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_validation"
    assert data["passed"]
    assert data["validated_entity_id"] == morphology_id
