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


def _assert_read_response(data, json_data):
    assert data["given_name"] == json_data["given_name"]
    assert data["family_name"] == json_data["family_name"]
    assert "id" in data
    assert data["sub_id"] == ANY


def test_create_person(client, client_admin, json_data):
    response = client_admin.post(ROUTE, json=json_data)
    assert response.status_code == 200
    data = response.json()
    _assert_read_response(data, json_data)

    id_ = data["id"]

    response = client.get(f"{ROUTE}/{id_}")
    assert response.status_code == 200
    data = response.json()
    _assert_read_response(data, json_data)
    assert data["id"] == id_

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

    valid_orcids = [
        "https://orcid.org/0000-0002-1825-0097",
        "https://orcid.org/0000-0003-1234-5674",
    ]

    for orcid in valid_orcids:
        data = assert_request(
            client_admin.post,
            url=ROUTE,
            json=json_data | {"orcid": orcid, "pref_label": f"person-{orcid[-4:]}"},
        ).json()
        assert data["orcid"] == orcid

    invalid_orcids = [
        "invalid-orcid",
        "1234-5678",
        "abcd-efgh-ijkl-mnop",
        "0000-0003-1234-5678",
        "0000-0002-1825-0097",
    ]

    for orcid in invalid_orcids:
        data = assert_request(
            client_admin.post,
            url=ROUTE,
            json=json_data | {"orcid": orcid, "pref_label": f"person-{orcid}"},
            expected_status_code=422,
        ).json()
        assert data["message"] == "Validation error"

    orcid = "https://orcid.org/0000-0004-5678-9012"
    assert_request(
        client_admin.post,
        url=ROUTE,
        json=json_data | {"orcid": orcid, "pref_label": "person-orcid-dup-1"},
    ).json()
    data = assert_request(
        client_admin.post,
        url=ROUTE,
        json=json_data | {"orcid": orcid, "pref_label": "person-orcid-dup-2"},
        expected_status_code=409,
    ).json()
    assert data["error_code"] == "ENTITY_DUPLICATED"


def test_read_many(clients, json_data):

    route = ROUTE
    admin_route = ADMIN_ROUTE

    assert_request(clients.admin.post, url=route, json=json_data).json()["id"]

    def _req(client, client_route):
        data = assert_request(client.get, url=client_route).json()["data"]
        assert len(data) == 2

    # user that created the resource can read it
    _req(clients.user_1, route)

    # but cannot use the admin endpoint
    data = assert_request(
        clients.user_1.get,
        url=admin_route,
        expected_status_code=403,
    ).json()
    assert data["message"] == "Service admin role required"

    # any other user can read it too because it is global
    _req(clients.user_2, route)

    # but cannot use the admin endpoint
    data = assert_request(
        clients.user_2.get,
        url=admin_route,
        expected_status_code=403,
    ).json()
    assert data["message"] == "Service admin role required"

    # service admins can read from both regular and admin routes
    _req(clients.admin, route)
    _req(clients.admin, admin_route)


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
                orcid="https://orcid.org/0000-0001-1111-110X",
                created_by_id=person_id,
                updated_by_id=person_id,
            ),
            Person(
                given_name="john",
                family_name="Cooper",
                pref_label="John Cooper",
                orcid="https://orcid.org/0000-0002-2222-2208",
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

    data = _req({"orcid": "https://orcid.org/0000-0001-1111-110X"})
    assert len(data) == 1
    assert data[0]["pref_label"] == "John Smith"

    data = _req({"orcid": "https://orcid.org/0000-0002-2222-2208"})
    assert len(data) == 1
    assert data[0]["pref_label"] == "John Cooper"

    data = _req(
        {
            "orcid__in": [
                "https://orcid.org/0000-0001-1111-110X",
                "https://orcid.org/0000-0002-2222-2208",
            ]
        }
    )
    assert len(data) == 2
    assert {d["pref_label"] for d in data} == {"John Smith", "John Cooper"}

    data = _req({"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1})
    assert len(data) == len(models) + 1  # +1 for person_id
