from app.config import settings


def test_root(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.next_request.url.path == f"{settings.ROOT_PATH}/docs"


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


def test_version(client):
    response = client.get("/version")

    assert response.status_code == 200
    response_json = response.json()
    assert set(response_json) == {"app_name", "app_version", "commit_sha"}
    assert response_json["app_name"] == "entitycore"
    assert response_json["app_version"] is not None
    assert response_json["commit_sha"] is not None


def test_error(client):
    response = client.get("/error")

    assert response.status_code == 400
    assert response.json() == {
        "error_code": "INVALID_REQUEST",
        "message": "Generic error returned for testing purposes",
        "details": None,
    }


def test_extra_query_params(client):
    response = client.get("/version", params={"foo": "bar"})

    assert response.status_code == 422
    assert response.json() == {
        "error_code": "INVALID_REQUEST",
        "message": "Unknown query parameters",
        "details": {"unknown_params": ["foo"]},
    }


def test_extra_query_params_bypass(client):
    response = client.get("/version", params={"foo": "bar", "allow_extra_params": True})

    assert response.status_code == 200
