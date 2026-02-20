from app.schemas.types import HeaderKey


def test_add_request_id_header(client_no_auth):
    response = client_no_auth.get("/health")
    assert response.status_code == 200
    assert HeaderKey.request_id in response.headers


def test_add_process_time_header(client_no_auth):
    response = client_no_auth.get("/health")
    assert response.status_code == 200
    assert HeaderKey.process_time in response.headers
    assert float(response.headers[HeaderKey.process_time]) >= 0
