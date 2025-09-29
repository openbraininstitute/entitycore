import pytest

from app.db.model import EModel, ETypeClass, ETypeClassification

from .utils import (
    PROJECT_ID,
    add_all_db,
    add_db,
    check_global_delete_one,
    check_global_read_one,
    check_global_update_one,
    check_missing,
    with_creation_fields,
)

ROUTE = "/etype"
ADMIN_ROUTE = "/admin/etype"
ROUTE_EMODEL = "/emodel"


@pytest.fixture
def json_data():
    return {
        "pref_label": "pref_label_etype",
        "alt_label": "alt_label_etype",
        "definition": "definition_etype",
    }


def _assert_read_response(data, json_data):
    assert "id" in data
    assert data["pref_label"] == json_data["pref_label"]
    assert data["alt_label"] == json_data["alt_label"]
    assert data["definition"] == json_data["definition"]
    assert "creation_date" in data
    assert "update_date" in data


def test_read_one(clients, json_data):
    check_global_read_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        validator=_assert_read_response,
    )


def test_update_one(clients, json_data):
    check_global_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        patch_payload={
            "pref_label": "new_pref_label_etype",
            "alt_label": "new_alt_label_etype",
            "definition": "new_definition_etype",
        },
    )


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
    etypes = add_all_db(
        db,
        [
            ETypeClass(**item | {"created_by_id": person_id, "updated_by_id": person_id})
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

    # backwards compat
    response = client.get(ROUTE, params={"pref_label__in": "pref_label_5,pref_label_6"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    assert data == [with_creation_fields(items[5]), with_creation_fields(items[6])]

    response = client.get(ROUTE, params={"pref_label__in": ["pref_label_5", "pref_label_6"]})
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


def test_emodel_etypes(
    db, client, species_id, strain_id, brain_region_id, morphology_id, person_id
):
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
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    ).id

    etype1_json = {
        "pref_label": "e1",
        "alt_label": "e1",
        "definition": "e1d",
    }
    etype2_json = {
        "pref_label": "e2",
        "alt_label": "e2",
        "definition": "e2d",
    }
    etype1 = add_db(
        db, ETypeClass(**etype1_json | {"created_by_id": person_id, "updated_by_id": person_id})
    )
    etype2 = add_db(
        db, ETypeClass(**etype2_json | {"created_by_id": person_id, "updated_by_id": person_id})
    )

    add_db(
        db,
        ETypeClassification(
            entity_id=emodel_id,
            etype_class_id=etype1.id,
            created_by_id=person_id,
            updated_by_id=person_id,
            authorized_public=False,
            authorized_project_id=PROJECT_ID,
        ),
    )
    add_db(
        db,
        ETypeClassification(
            entity_id=emodel_id,
            etype_class_id=etype2.id,
            created_by_id=person_id,
            updated_by_id=person_id,
            authorized_public=False,
            authorized_project_id=PROJECT_ID,
        ),
    )

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


def test_delete_one(db, clients, json_data):
    check_global_delete_one(
        db=db,
        clients=clients,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        json_data=json_data,
        expected_counts_before={
            ETypeClass: 1,
        },
        expected_counts_after={
            ETypeClass: 0,
        },
    )
