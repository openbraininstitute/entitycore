from unittest.mock import ANY

from app.db.model import MTypeClass, MTypeClassification

from .utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    add_all_db,
    add_db,
    create_reconstruction_morphology_id,
)

ROUTE = "/mtype"
ROUTE_MORPH = "/reconstruction-morphology"


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
    mtypes = add_all_db(db, [MTypeClass(**item) for item in items])

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

    response = client.get(f"{ROUTE}/{mtypes[0].id}")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(mtypes[0].id)
    assert data["pref_label"] == "pref_label_0"
    assert data["alt_label"] == "alt_label_0"
    assert data["definition"] == "definition_0"


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422


def test_morph_mtypes(db, client, species_id, strain_id, brain_region_id):
    morph_id = create_reconstruction_morphology_id(
        client,
        species_id,
        strain_id,
        brain_region_id,
        authorized_public=False,
    )

    mtype1 = add_db(db, MTypeClass(pref_label="m1", alt_label="m1", definition="m1d"))
    mtype2 = add_db(db, MTypeClass(pref_label="m2", alt_label="m2", definition="m2d"))

    add_db(db, MTypeClassification(entity_id=morph_id, mtype_class_id=mtype1.id))
    add_db(db, MTypeClassification(entity_id=morph_id, mtype_class_id=mtype2.id))

    response = client.get(ROUTE_MORPH, params={"with_facets": True})
    assert response.status_code == 200
    facets = response.json()["facets"]
    assert facets["mtype"] == [
        {"id": str(mtype1.id), "label": "m1", "count": 1, "type": "mtype"},
        {"id": str(mtype2.id), "label": "m2", "count": 1, "type": "mtype"},
    ]

    response = client.get(f"{ROUTE_MORPH}/{morph_id}")
    assert response.status_code == 200
    data = response.json()
    assert "mtypes" in data
    mtypes = data["mtypes"]
    assert len(mtypes) == 2

    assert mtypes == [
        {
            "id": str(mtype1.id),
            "pref_label": "m1",
            "alt_label": "m1",
            "definition": "m1d",
            "creation_date": ANY,
            "update_date": ANY,
        },
        {
            "id": str(mtype2.id),
            "pref_label": "m2",
            "alt_label": "m2",
            "definition": "m2d",
            "creation_date": ANY,
            "update_date": ANY,
        },
    ]

    response = client.get(ROUTE_MORPH, params={"with_facets": True, "mtype__pref_label": "m1"})
    assert response.status_code == 200
    facets = response.json()["facets"]
    assert facets["mtype"] == [
        {"id": str(mtype1.id), "label": "m1", "count": 1, "type": "mtype"},
    ]
