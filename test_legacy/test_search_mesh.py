from . import TEST_SEARCH_END_POINT, get_body

def test_search_mesh(client):
    print(TEST_SEARCH_END_POINT + "/_search")
    response = client.post(
        TEST_SEARCH_END_POINT + "/_search",
        json=get_body("search_mesh"),
    )
    assert response.status_code == 200
    data = response.json()["hits"]["hits"]
    assert len(data) > 600 
    assert data[0]["_id"] == data[0]["_source"]["@id"]
    source = data[0]["_source"]
    assert source["@type"] == ["Mesh"]
    assert source.get("brainLocation").get("brainRegion") is not None
    assert source.get("distribution").get("content_url") is not None