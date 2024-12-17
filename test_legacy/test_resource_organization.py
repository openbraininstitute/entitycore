def test_resource_organization(client):
    response = client.get(
        "/nexus/v1/resources/public/sscx/_/https%3A%2F%2Fwww.grid.ac%2Finstitutes%2Fgrid.5333.6"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "École Polytechnique Fédérale de Lausanne"
    assert data["@id"] == "https://www.grid.ac/institutes/grid.5333.6"
    assert data["@type"] == "Organization"
