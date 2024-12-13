from . import TEST_SEARCH_END_POINT, get_body

def test_create_license(client):
    print(TEST_SEARCH_END_POINT + "/_search")
    response = client.post(
        TEST_SEARCH_END_POINT + "/_search",
        json=get_body("license_by_id"),
    )
    assert response.status_code == 200
    data = response.json()["hits"]["hits"]
    assert len(data) == 1
    assert data[0]["_id"] == "https://creativecommons.org/licenses/by/4.0/"
    assert data[0]["_source"]["@id"] == "https://creativecommons.org/licenses/by/4.0/"
    assert data[0]["_source"]["@type"] == ["License"]
    assert data[0]["_source"]["label"] == "CC BY 4.0 Deed"