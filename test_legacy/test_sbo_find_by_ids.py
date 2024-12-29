from . import TEST_SBO_END_POINT, get_body


def test_sbo_find_by_ids(client):
    response = client.post(
        TEST_SBO_END_POINT,
        json=get_body("sbo_find_by_ids"),
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["hits"]["total"]["value"], int)
    assert data["hits"]["total"]["value"] == 8