from . import TEST_SEARCH_END_POINT, get_body


def test_search_generator_task_activity(client):
    response = client.post(
        TEST_SEARCH_END_POINT + "/_search",
        json=get_body("search_generator_task_activity"),
    )
    assert response.status_code == 200
    data = response.json()["hits"]["hits"]
    assert len(data) == 1
    assert data[0]["_id"] == data[0]["_source"]["@id"]
    assert data[0]["_source"]["@type"] == "GeneratorTaskActivity"
