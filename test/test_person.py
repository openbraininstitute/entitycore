def test_create_person(client):
    response = client.post(
        "/person/", json={"first_name": "jd", "last_name": "courcol"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "jd"
    assert data["last_name"] == "courcol"
    assert "id" in data
    id_ = data["id"]
    response = client.get(f"/person/{id_}")
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "jd"
    assert data["id"] == id_
    response = client.get("/person/")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["first_name"] == "jd"
    assert data[0]["id"] == id_
    assert len(data) == 1
