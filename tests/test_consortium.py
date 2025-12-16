import pytest

from app.db.model import Consortium

from tests.utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    USER_SUB_ID_1,
    add_db,
    assert_request,
    check_global_delete_one,
)

ROUTE = "/consortium"
ADMIN_ROUTE = "/admin/consortium"


@pytest.fixture
def json_data():
    return {
        "pref_label": "test consortium label",
        "alternative_name": "test consortium alternative name",
    }


def test_create(client, client_admin, json_data):
    response = client_admin.post(ROUTE, json=json_data)
    assert response.status_code == 200
    data = response.json()
    assert data["pref_label"] == json_data["pref_label"]
    assert data["alternative_name"] == json_data["alternative_name"]
    assert "id" in data
    id_ = data["id"]

    response = client.get(f"{ROUTE}/{id_}")
    assert response.status_code == 200
    data = response.json()
    assert data["pref_label"] == json_data["pref_label"]
    assert data["alternative_name"] == json_data["alternative_name"]
    assert data["id"] == id_

    response = client.get(ROUTE)
    assert response.status_code == 200

    data = response.json()["data"]
    assert data[0]["id"] == id_
    assert len(data) == 1


def test_delete_one(db, clients, json_data):
    check_global_delete_one(
        db=db,
        clients=clients,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        json_data=json_data,
        expected_counts_before={
            Consortium: 1,
        },
        expected_counts_after={
            Consortium: 0,
        },
    )


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422


@pytest.fixture
def models(db, person_id):
    res = []
    for i in range(3):
        row = add_db(
            db,
            Consortium(
                pref_label=f"org-{i}",
                alternative_name=f"alt-{i}",
                created_by_id=person_id,
                updated_by_id=person_id,
            ),
        )
        res.append(row)
    return res


def test_filtering_sorting(client, models):
    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    data = req({"order_by": "creation_date"})
    assert len(data) == len(models)

    data = req({"pref_label__ilike": "org"})
    assert len(data) == len(models)

    data = req({"pref_label__in": ["org-1", "org-2"], "order_by": "-creation_date"})
    assert [d["pref_label"] for d in data] == ["org-2", "org-1"]

    data = req({"alternative_name": "alt-1", "order_by": "creation_date"})
    assert [d["alternative_name"] for d in data] == ["alt-1"]

    data = req(
        {
            "created_by__sub_id": USER_SUB_ID_1,
            "updated_by__sub_id": USER_SUB_ID_1,
            "order_by": "creation_date",
        }
    )
    assert len(data) == len(models)
