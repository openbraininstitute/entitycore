
from . import TEST_SBO_END_POINT, get_body


def test_sbo_reconstruction_morphology(client):
    response = client.post(
        TEST_SBO_END_POINT,
        json=get_body("sbo_count_with_term_region"),
    )
    assert response.status_code == 200
    data = response.json()
    assert type(data['hits']['total']['value']) == int
    assert data['hits']['total']['value'] < 450 
    assert data['hits']['total']['value'] > 100