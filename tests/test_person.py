from unittest.mock import ANY

import pytest

from app.db.model import Agent, Person

from tests.utils import (
    ADMIN_SUB_ID,
    MISSING_ID,
    MISSING_ID_COMPACT,
    USER_SUB_ID_1,
    add_all_db,
    assert_request,
    check_global_delete_one,
)

ROUTE = "/person"
ADMIN_ROUTE = "/admin/person"


@pytest.fixture
def json_data():
    return {
        "given_name": "jd",
        "family_name": "courcol",
        "pref_label": "jd courcol",
    }


def test_create_person(client, client_admin, json_data):
    response = client_admin.post(ROUTE, json=json_data)
    assert response.status_code == 200
    data = response.json()
    assert data["given_name"] == json_data["given_name"]
    assert data["family_name"] == json_data["family_name"]
    assert "id" in data
    id_ = data["id"]
    assert data["sub_id"] == ANY

    response = client.get(f"{ROUTE}/{id_}")
    assert response.status_code == 200
    data = response.json()
    assert data["given_name"] == json_data["given_name"]
    assert data["id"] == id_
    assert data["sub_id"] == ANY

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]

    # Two people are expected, the registered one without a subject id
    # and the new agent registered from the token with a subject id
    assert len(data) == 2

    created_from_data, created_from_token = _classify_agents(data)

    assert created_from_data["given_name"] == json_data["given_name"]
    assert created_from_data["id"] == id_
    assert created_from_data["sub_id"] is None

    assert created_from_token["pref_label"] == "Admin User"
    assert created_from_token["sub_id"] == str(ADMIN_SUB_ID)

    # If register again only the data agent added and the token agent is reused
    response = client_admin.post(
        ROUTE,
        json=json_data,
    )
    assert response.status_code == 200

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]

    assert len(data) == 3
    assert sum(1 for d in data if d["sub_id"] is not None) == 1


def test_delete_one(db, clients, json_data):
    check_global_delete_one(
        db=db,
        clients=clients,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        json_data=json_data,
        expected_counts_before={
            Person: 2,
            Agent: 2,
        },
        expected_counts_after={
            Person: 1,
            Agent: 1,
        },
    )


def _classify_agents(data):
    if data[0]["sub_id"] is None:
        return data

    return data[1], data[0]


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
    return add_all_db(
        db,
        [
            Person(
                given_name="John",
                family_name="Smith",
                pref_label="John Smith",
                created_by_id=person_id,
                updated_by_id=person_id,
            ),
            Person(
                given_name="john",
                family_name="Cooper",
                pref_label="John Cooper",
                created_by_id=person_id,
                updated_by_id=person_id,
            ),
            Person(
                given_name="Beatrix",
                family_name="John",
                pref_label="Beatrix John",
                created_by_id=person_id,
                updated_by_id=person_id,
            ),
        ],
    )


def test_filtering(client, models):
    def _req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    data = _req({"id__in": [str(m.id) for m in models]})
    assert len(data) == len(models)

    data = _req({"pref_label__ilike": "John"})
    assert len(data) == 3

    data = _req({"given_name__ilike": "John"})
    assert len(data) == 2

    data = _req({"family_name__ilike": "Smith"})
    assert len(data) == 1

    data = _req({"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1})
    assert len(data) == len(models) + 1  # +1 for person_id
