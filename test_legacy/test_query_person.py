def test_query_person(client):
    response = client.get(
        "/nexus/v1/resources/bbp/mmb-point-neuron-framework-model/_/https%3A%2F%2Fbbp.epfl.ch%2Fnexus%2Fv1%2Frealms%2Fbbp%2Fusers%2Fkanari"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["familyName"] == "Kanari"
    assert data["givenName"] == "Lida"
    assert data["@id"] == "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/kanari"
  
  