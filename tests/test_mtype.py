from app.db.model import MTypeAnnotationBody

ROUTE = "/mtype/"


def test_mtype(db, client):
    count = 10

    for i in range(count):
        row = MTypeAnnotationBody(
            pref_label=f"pref_label_{i}",
            alt_label=f"alt_label_{i}",
            definition=f"definition_{i}",
        )
        db.add(row)
    db.commit()

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()

    assert len(data) == count
    assert data[0]["pref_label"] == "pref_label_0"
    assert data[0]["alt_label"] == "alt_label_0"
    assert data[0]["definition"] == "definition_0"

    response = client.get(ROUTE + "1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["pref_label"] == "pref_label_0"
    assert data["alt_label"] == "alt_label_0"
    assert data["definition"] == "definition_0"


def test_missing_mtype(client):
    response = client.get(ROUTE + "42424242")
    assert response.status_code == 404

    response = client.get(ROUTE + "notanumber")
    assert response.status_code == 422
