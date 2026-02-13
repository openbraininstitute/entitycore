from app.db.model import CellMorphology, License

from tests.utils import PROJECT_ID, add_all_db, check_sort_by_field

ROUTE_LICENSE = "/license"
ROUTE_MORPHOLOGY = "/cell-morphology"


def test_license_ordering(db, client, person_id):
    count = 10
    items = [
        {"name": f"name_{i}", "label": f"label_{i}", "description": f"description_{i}"}
        for i in range(count)
    ]
    add_all_db(
        db,
        [
            License(**item | {"created_by_id": person_id, "updated_by_id": person_id})
            for item in items
        ],
        same_transaction=True,
    )

    response = client.get(ROUTE_LICENSE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == count
    assert all(d["creation_date"] == data[0]["creation_date"] for d in data)
    check_sort_by_field(data, "id")


def test_cell_morphology_ordering(db, client, subject_id, license_id, brain_region_id, person_id):
    count = 10
    items = [
        {
            "name": f"name_{i}" if i < count / 2 else f"name_to_find_{i}",
            "description": f"description_{i}",
            "brain_region_id": str(brain_region_id),
            "subject_id": str(subject_id),
            "location": {"x": 10, "y": 20, "z": 30},
            "license_id": str(license_id),
            "legacy_id": ["Test Legacy ID"],
            "created_by_id": person_id,
            "updated_by_id": person_id,
            "authorized_project_id": PROJECT_ID,
        }
        for i in range(count)
    ]

    add_all_db(
        db,
        [CellMorphology(**item) for item in items],
        same_transaction=True,
    )

    response = client.get(ROUTE_MORPHOLOGY)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == count
    assert all(d["creation_date"] == data[0]["creation_date"] for d in data)
    check_sort_by_field(data, "id")

    response = client.get(ROUTE_MORPHOLOGY, params={"name__ilike": "to_find"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == count // 2
    check_sort_by_field(data, "id")

    response = client.get(ROUTE_MORPHOLOGY, params={"name__ilike": "to_find", "order_by": "name"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == count // 2
    check_sort_by_field(data, "name")

    response = client.get(ROUTE_MORPHOLOGY, params={"name__ilike": "to_find", "order_by": "-name"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == count // 2
    check_sort_by_field(data, "name", how="descending")
