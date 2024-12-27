from . import TEST_SBO_END_POINT, get_body


def test_sbo_faceted_search_with_term_region(client):
    response = client.post(
        TEST_SBO_END_POINT,
        json=get_body("sbo_faceted_search_with_term_region"),
    )
    assert response.status_code == 200
    data = response.json()
    assert set(data["aggregations"].keys()) == set(
        [
            "contributors",
            "mType",
            "subjectSpecies",
        ]
    )
    for elem in data["aggregations"].values():
        assert len(elem["buckets"]) > 0
        prev_value = None
        for bucket in elem["buckets"]:
            assert type(bucket["key"]) == str
            assert type(bucket["doc_count"]) == int
            if prev_value:
                assert prev_value >= bucket["doc_count"]
            prev_value = bucket["doc_count"]
    assert len(data["hits"]["hits"]) > 0
    assert len(data["hits"]["hits"]) < 31
