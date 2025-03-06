from app.db.model import MTypeClass

ROUTE = "/mtype"


def test_mtype(db, client):
    count = 10
    items = [
        {
            "pref_label": f"pref_label_{i}",
            "alt_label": f"alt_label_{i}",
            "definition": f"definition_{i}",
        }
        for i in range(count)
    ]
    db.add_all(MTypeClass(**item) for item in items)
    db.commit()

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]

    assert len(data) == count
    assert data[0]["pref_label"] == "pref_label_0"
    assert data[0]["alt_label"] == "alt_label_0"
    assert data[0]["definition"] == "definition_0"

    # test filter (eq)
    response = client.get(ROUTE, params={"pref_label": "pref_label_5"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["pref_label"] == items[5]["pref_label"]
    assert data[0]["alt_label"] == items[5]["alt_label"]
    assert data[0]["definition"] == items[5]["definition"]

    # test filter (in)
    response = client.get(ROUTE, params={"pref_label__in": "pref_label_5,pref_label_6"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    assert data[0]["pref_label"] == items[5]["pref_label"]
    assert data[0]["alt_label"] == items[5]["alt_label"]
    assert data[0]["definition"] == items[5]["definition"]
    assert data[1]["pref_label"] == items[6]["pref_label"]
    assert data[1]["alt_label"] == items[6]["alt_label"]
    assert data[1]["definition"] == items[6]["definition"]

    response = client.get(f"{ROUTE}/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["pref_label"] == "pref_label_0"
    assert data["alt_label"] == "alt_label_0"
    assert data["definition"] == "definition_0"


def test_missing_mtype(client):
    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422
