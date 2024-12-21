from . import TEST_SEARCH_END_POINT, get_body


def test_search_mtype_type(client):
    print(TEST_SEARCH_END_POINT + "/_search")
    response = client.post(
        TEST_SEARCH_END_POINT + "/_search",
        json=get_body("search_mtype_etype"),
    )
    assert response.status_code == 200
    data = response.json()["hits"]["hits"]
    print(data[0])
    ids = [d["_id"] for d in data]
    ids_source = [d["_source"]["@id"] for d in data]
    assert set(ids) == set(ids_source)
    labels = [d["_source"]["label"] for d in data]
    assert len(labels) == len(ids)
