def test_create_person(client):
    response = client.post(
        "/person/",
        json={"givenName": "jd", "familyName": "courcol", "pref_label": "jd courcol"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["givenName"] == "jd"
    assert data["familyName"] == "courcol"
    assert "id" in data
    id_ = data["id"]
    response = client.get(f"/person/{id_}")
    assert response.status_code == 200
    data = response.json()
    assert data["givenName"] == "jd"
    assert data["id"] == id_
    response = client.get("/person/")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["givenName"] == "jd"
    assert data[0]["id"] == id_
    assert len(data) == 1


def test_missing_person(client):
    response = client.get("/person/42424242")
    assert response.status_code == 404

    response = client.get("/person/notanumber")
    assert response.status_code == 422
