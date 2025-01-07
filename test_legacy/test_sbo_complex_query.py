from . import TEST_SBO_END_POINT, get_body


def test_sbo_complex_query(client):
    response = client.post(
        TEST_SBO_END_POINT,
        json=get_body("sbo_complex_query"),
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
    assert len(data["hits"]["hits"]) == 25
    assert len(data["aggregations"]["mType"]["buckets"]) == 1
    assert len(data["aggregations"]["subjectSpecies"]["buckets"]) == 1
    assert data["aggregations"]["mType"]["buckets"][0]["key"] == "SP_PC"
    assert (
        data["aggregations"]["subjectSpecies"]["buckets"][0]["key"]
        == "Rattus norvegicus"
    )
