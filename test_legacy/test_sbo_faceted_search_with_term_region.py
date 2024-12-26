from . import TEST_SBO_END_POINT, get_body


def test_sbo_reconstruction_morphology(client):
    response = client.post(
        TEST_SBO_END_POINT,
        json=get_body("sbo_faceted_search_with_term_region"),
    )
    assert response.status_code == 200
    data = response.json()
    # Vassert type(data['hits']['total']['value']) == int
    # assert data['hits']['total']['value'] < 450 
    # assert data['hits']['total']['value'] > 100
    assert set(data['aggregations'].keys()) == set(["contributors", "mType", "subjectSpecies",])