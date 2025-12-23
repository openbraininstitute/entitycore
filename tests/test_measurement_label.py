import pytest

from app.db.model import MeasurementLabel
from app.db.types import EntityType

from .utils import check_creation_fields, check_missing
from tests.utils import (
    USER_SUB_ID_1,
    add_all_db,
    assert_request,
    check_global_delete_one,
    check_global_read_one,
    check_global_update_one,
)

ROUTE = "/measurement-label"
ADMIN_ROUTE = "/admin/measurement-label"


@pytest.fixture
def json_data():
    return {
        "entity_type": EntityType.cell_morphology,
        "pref_label": "my_label",
        "definition": "my_definition",
    }


def _assert_read_response(data, json_data):
    assert "id" in data
    assert data["pref_label"] == json_data["pref_label"]
    assert data["definition"] == json_data["definition"]
    assert "created_by" in data
    assert "updated_by" in data


def test_create_one(client, client_admin):
    count = 3
    items = []
    for i in range(count):
        request_payload = {
            "entity_type": EntityType.cell_morphology,
            "pref_label": f"test_pref_label_{i}",
            "definition": f"Test definition {i}",
        }
        response = client_admin.post(ROUTE, json=request_payload)
        assert response.status_code == 200
        data = response.json()
        _assert_read_response(data, request_payload)
        check_creation_fields(data)
        assert "id" in data
        items.append(data)

    response = client.get(f"{ROUTE}/{items[0]['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data == items[0]
    check_creation_fields(data)

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == count
    assert data == list(reversed(items))
    check_creation_fields(data[0])

    # test filter
    response = client.get(ROUTE, params={"pref_label": "test_pref_label_1"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data == [items[1]]
    check_creation_fields(data[0])


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
            "pref_label": "my-new-label",
            "definition": "",
        },
    )


def test_delete_one(db, clients, json_data):
    check_global_delete_one(
        db=db,
        clients=clients,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        json_data=json_data,
        expected_counts_before={
            MeasurementLabel: 1,
        },
        expected_counts_after={
            MeasurementLabel: 0,
        },
    )


def test_missing(client):
    check_missing(ROUTE, client)


@pytest.fixture
def models(db, json_data, person_id):
    objs = [
        MeasurementLabel(
            **json_data
            | {
                "pref_label": f"label_{i}",
                "definition": f"Definition {i}",
                "created_by_id": person_id,
                "updated_by_id": person_id,
            }
        )
        for i in range(3)
    ]

    return add_all_db(db, objs)


def test_filtering(client, models):
    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    data = req({"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1})
    assert len(data) == len(models)
