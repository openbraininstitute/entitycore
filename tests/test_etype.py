from app.db.model import EModel, ETypeClass, ETypeClassification

from .utils import (
    PROJECT_ID,
    add_all_db,
    add_db,
    check_missing,
    with_creation_fields,
)

ROUTE = "/etype"
ROUTE_EMODEL = "/emodel"


def test_retrieve(db, client):
    count = 10
    items = [
        {
            "pref_label": f"pref_label_{i}",
            "alt_label": f"alt_label_{i}",
            "definition": f"definition_{i}",
        }
        for i in range(count)
    ]
    etypes = add_all_db(db, [ETypeClass(**item) for item in items])

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

    response = client.get(f"{ROUTE}/{etypes[0].id}")
    assert response.status_code == 200
    data = response.json()

    assert data == with_creation_fields(items[0]) | {"id": str(etypes[0].id)}


def test_missing(client):
    check_missing(ROUTE, client)


def test_emodel_etypes(db, client, species_id, strain_id, brain_region_id, morphology_id):
    emodel_id = add_db(
        db,
        EModel(
            name="Test name",
            description="Test description",
            brain_region_id=brain_region_id,
            species_id=species_id,
            strain_id=strain_id,
            exemplar_morphology_id=morphology_id,
            authorized_public=False,
            authorized_project_id=PROJECT_ID,
        ),
    ).id

    etype1_json = {"pref_label": "e1", "alt_label": "e1", "definition": "e1d"}
    etype2_json = {"pref_label": "e2", "alt_label": "e2", "definition": "e2d"}
    etype1 = add_db(db, ETypeClass(**etype1_json))
    etype2 = add_db(db, ETypeClass(**etype2_json))

    add_db(db, ETypeClassification(entity_id=emodel_id, etype_class_id=etype1.id))
    add_db(db, ETypeClassification(entity_id=emodel_id, etype_class_id=etype2.id))

    response = client.get(ROUTE_EMODEL, params={"with_facets": True})
    assert response.status_code == 200
    facets = response.json()["facets"]
    assert facets["etype"] == [
        {"id": str(etype1.id), "label": "e1", "count": 1, "type": "etype"},
        {"id": str(etype2.id), "label": "e2", "count": 1, "type": "etype"},
    ]

    response = client.get(f"{ROUTE_EMODEL}/{emodel_id}")
    assert response.status_code == 200
    data = response.json()
    assert "etypes" in data
    etypes = data["etypes"]
    assert len(etypes) == 2

    assert etypes == [
        with_creation_fields(etype1_json) | {"id": str(etype1.id)},
        with_creation_fields(etype2_json) | {"id": str(etype2.id)},
    ]

    response = client.get(ROUTE_EMODEL, params={"with_facets": True, "etype__pref_label": "e1"})
    assert response.status_code == 200
    facets = response.json()["facets"]
    assert facets["etype"] == [
        {"id": str(etype1.id), "label": "e1", "count": 1, "type": "etype"},
    ]
