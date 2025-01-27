from . import TEST_SBO_END_POINT, get_body


def test_sbo_facets(client):
    response = client.post(
        TEST_SBO_END_POINT,
        json=get_body("sbo_facets"),
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["aggregations"]["contributors"]["buckets"]) == 2
    for item in data["aggregations"]["contributors"]["buckets"]:
        assert isinstance(item["key"], str)
        assert isinstance(item["doc_count"], int)

    assert (
        data["aggregations"]["contributors"]["buckets"][0]["key"] == "Aur\u00e9lien Tristan Jaquier"
    )
    # TODO: fix Ilkan's name
    # assert data["aggregations"]["contributors"]["buckets"][1]["key"] == "Ilkan Fabrice Kili\u00e7"
    # TODO: understand why 17 in imported data.
    # assert len(data["aggregations"]["eType"]["buckets"]) == 18
