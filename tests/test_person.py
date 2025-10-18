from unittest.mock import ANY

import pytest

from app.db.model import Agent, Person

from tests.utils import (
    ADMIN_SUB_ID,
    MISSING_ID,
    MISSING_ID_COMPACT,
    add_all_db,
    assert_request,
    count_db_class,
)

ROUTE = "/person"
ADMIN_ROUTE = "/admin/person"


def test_create_person(client, client_admin):
    response = client_admin.post(
        ROUTE,
        json={"given_name": "jd", "family_name": "courcol", "pref_label": "jd courcol"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["given_name"] == "jd"
    assert data["family_name"] == "courcol"
    assert "id" in data
    id_ = data["id"]
    assert data["sub_id"] == ANY

    response = client.get(f"{ROUTE}/{id_}")
    assert response.status_code == 200
    data = response.json()
    assert data["given_name"] == "jd"
    assert data["id"] == id_
    assert data["sub_id"] == ANY

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]

    # Two people are expected, the registered one without a subject id
    # and the new agent registered from the token with a subject id
    assert len(data) == 2

    created_from_data, created_from_token = _classify_agents(data)

    assert created_from_data["given_name"] == "jd"
    assert created_from_data["id"] == id_
    assert created_from_data["sub_id"] is None

    assert created_from_token["pref_label"] == "Admin User"
    assert created_from_token["sub_id"] == str(ADMIN_SUB_ID)

    # If register again only the data agent added and the token agent is reused
    response = client_admin.post(
        ROUTE,
        json={"given_name": "jd", "family_name": "courcol", "pref_label": "jd courcol"},
    )
    assert response.status_code == 200

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]

    assert len(data) == 3
    assert sum(1 for d in data if d["sub_id"] is not None) == 1


def test_delete_one(db, client, client_admin):
    response = client_admin.post(
        ROUTE,
        json={"given_name": "jd", "family_name": "courcol", "pref_label": "jd courcol"},
    )
    assert response.status_code == 200
    data = response.json()

    model_id = data["id"]

    # 1 created_by/updated_by 1 Person
    assert count_db_class(db, Person) == 2
    assert count_db_class(db, Agent) == 2

    data = assert_request(
        client.delete, url=f"{ADMIN_ROUTE}/{model_id}", expected_status_code=403
    ).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    data = assert_request(client_admin.delete, url=f"{ADMIN_ROUTE}/{model_id}").json()
    assert data["id"] == str(model_id)

    assert count_db_class(db, Person) == 1
    assert count_db_class(db, Agent) == 1


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
