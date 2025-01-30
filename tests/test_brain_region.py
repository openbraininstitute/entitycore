ROUTE = "/brain-regions/"


def test_get_brain_region(client):
    response = client.get(ROUTE)
    assert response.status_code == 200
    assert len(response.text) > 4_500_000
