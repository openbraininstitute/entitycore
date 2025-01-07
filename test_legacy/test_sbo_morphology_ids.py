from . import TEST_SBO_END_POINT, get_body


def test_sbo_morphology_ids(client):
    response = client.post(
        TEST_SBO_END_POINT,
        json=get_body("sbo_morphology_ids"),
    )
    assert response.status_code == 200
    data = response.json()
