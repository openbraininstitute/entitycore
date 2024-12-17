from . import TEST_SBO_END_POINT, get_body


def test_sbo_morphology_ids(client):
    response = client.post(
        TEST_SBO_END_POINT + "/_search",
        json=get_body("license_by_id"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "École Polytechnique Fédérale de Lausanne"
    assert data["@id"] == "https://www.grid.ac/institutes/grid.5333.6"
    assert data["@type"] == "Organization"
