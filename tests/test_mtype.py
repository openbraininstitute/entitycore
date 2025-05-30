from app.db.model import MTypeClass, MTypeClassification

from .utils import (
    add_all_db,
    add_db,
    check_missing,
    create_reconstruction_morphology_id,
    with_creation_fields,
)

ROUTE = "/mtype"
ROUTE_MORPH = "/reconstruction-morphology"


def test_retrieve(db, client, person_id):
    count = 10
    items = [
        {
            "pref_label": f"pref_label_{i}",
            "alt_label": f"alt_label_{i}",
            "definition": f"definition_{i}",
        }
        for i in range(count)
    ]
    mtypes = add_all_db(
        db,
        [
            MTypeClass(**item | {"created_by_id": person_id, "updated_by_id": person_id})
            for item in items
        ],
    )

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]

    assert len(data) == count
    assert data[0] == with_creation_fields(items[0])

    # test filter (eq)
    response = client.get(ROUTE, params={"pref_label": "pref_label_5"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0] == with_creation_fields(items[5])

    # test filter (in)
    response = client.get(ROUTE, params={"pref_label__in": "pref_label_5,pref_label_6"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    assert data == [with_creation_fields(items[5]), with_creation_fields(items[6])]

    response = client.get(f"{ROUTE}/{mtypes[0].id}")
    assert response.status_code == 200
    data = response.json()

    assert data == with_creation_fields(items[0]) | {"id": str(mtypes[0].id)}


def test_missing(client):
    check_missing(ROUTE, client)


def test_morph_mtypes(db, client, species_id, strain_id, brain_region_id, person_id):
    morph_id = create_reconstruction_morphology_id(
        client,
        species_id,
        strain_id,
        brain_region_id,
        authorized_public=False,
    )

    mtype1_json = {
        "pref_label": "m1",
        "alt_label": "m1",
        "definition": "m1d",
    }
    mtype2_json = {
        "pref_label": "m2",
        "alt_label": "m2",
        "definition": "m2d",
    }
    mtype1 = add_db(
        db, MTypeClass(**mtype1_json | {"created_by_id": person_id, "updated_by_id": person_id})
    )
    mtype2 = add_db(
        db, MTypeClass(**mtype2_json | {"created_by_id": person_id, "updated_by_id": person_id})
    )

    add_db(
        db,
        MTypeClassification(
            entity_id=morph_id,
            mtype_class_id=mtype1.id,
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )
    add_db(
        db,
        MTypeClassification(
            entity_id=morph_id,
            mtype_class_id=mtype2.id,
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )

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
        with_creation_fields(mtype1_json) | {"id": str(mtype1.id)},
        with_creation_fields(mtype2_json) | {"id": str(mtype2.id)},
    ]

    response = client.get(ROUTE_MORPH, params={"with_facets": True, "mtype__pref_label": "m1"})
    assert response.status_code == 200
    facets = response.json()["facets"]
    assert facets["mtype"] == [
        {"id": str(mtype1.id), "label": "m1", "count": 1, "type": "mtype"},
    ]
