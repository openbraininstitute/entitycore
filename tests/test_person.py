import uuid

import pytest

from app.db.model import Agent, Person, PlatformUser

from tests.utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    USER_SUB_ID_1,
    add_all_db,
    add_db,
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
    assert "sub_id" in data


def test_create_person(client, json_data):
    response = client.post(ROUTE, json=json_data)
    assert response.status_code == 200
    data = response.json()
    _assert_read_response(data, json_data)

    id_ = data["id"]

    response = client.get(f"{ROUTE}/{id_}")
    assert response.status_code == 200
    data = response.json()
    _assert_read_response(data, json_data)
    assert data["id"] == id_

    valid_orcids = [
        "https://orcid.org/0000-0002-1825-0097",
        "https://orcid.org/0000-0003-1234-5674",
    ]

    for orcid in valid_orcids:
        data = assert_request(
            client.post,
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
            client.post,
            url=ROUTE,
            json=json_data | {"orcid": orcid, "pref_label": f"person-{orcid}"},
            expected_status_code=422,
        ).json()
        assert data["message"] == "Validation error"

    orcid = "https://orcid.org/0000-0004-5678-9012"
    assert_request(
        client.post,
        url=ROUTE,
        json=json_data | {"orcid": orcid, "pref_label": "person-orcid-dup-1"},
    ).json()
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data | {"orcid": orcid, "pref_label": "person-orcid-dup-2"},
        expected_status_code=409,
    ).json()
    assert data["error_code"] == "ENTITY_DUPLICATED"


def test_read_many(clients, json_data):
    route = ROUTE
    admin_route = ADMIN_ROUTE

    assert_request(clients.user_1.post, url=route, json=json_data).json()["id"]

    def _req(client, client_route):
        data = assert_request(client.get, url=client_route).json()["data"]
        # 2 persons: auto-created (from get_or_create_user) + explicitly created
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
            # 2 persons: auto-created (from get_or_create_user) + explicitly created
            Person: 2,
            Agent: 2,
        },
        expected_counts_after={
            Person: 1,
            Agent: 1,
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
def models(db, user_id):
    return add_all_db(
        db,
        [
            Person(
                given_name="John",
                family_name="Smith",
                pref_label="John Smith",
                orcid="https://orcid.org/0000-0001-1111-110X",
                created_by_id=user_id,
                updated_by_id=user_id,
            ),
            Person(
                given_name="john",
                family_name="Cooper",
                pref_label="John Cooper",
                orcid="https://orcid.org/0000-0002-2222-2208",
                created_by_id=user_id,
                updated_by_id=user_id,
            ),
            Person(
                given_name="Beatrix",
                family_name="John",
                pref_label="Beatrix John",
                created_by_id=user_id,
                updated_by_id=user_id,
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

    data = _req({"created_by__id": USER_SUB_ID_1, "updated_by__id": USER_SUB_ID_1})
    assert len(data) == len(models)

    data = _req({"created_by__id__in": [USER_SUB_ID_1], "updated_by__id__in": [USER_SUB_ID_1]})
    assert len(data) == len(models)

    # backward compat: sub_id is an alias for id
    data = _req({"created_by__sub_id": USER_SUB_ID_1})
    assert len(data) == len(models)

    data = _req({"created_by__sub_id__in": [USER_SUB_ID_1]})
    assert len(data) == len(models)


def test_sub_id_filtering(db, client, user_id):
    sub = uuid.uuid4()
    add_db(
        db,
        PlatformUser(id=sub, pref_label="linked user"),
    )
    person = add_db(
        db,
        Person(
            given_name="Linked",
            family_name="User",
            pref_label="Linked User",
            sub_id=sub,
            created_by_id=user_id,
            updated_by_id=user_id,
        ),
    )
    add_db(
        db,
        Person(
            given_name="Unlinked",
            family_name="Person",
            pref_label="Unlinked Person",
            created_by_id=user_id,
            updated_by_id=user_id,
        ),
    )

    def _req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    data = _req({"sub_id": str(sub)})
    assert len(data) == 1
    assert data[0]["id"] == str(person.id)
    assert data[0]["sub_id"] == str(sub)

    data = _req({"sub_id__in": [str(sub)]})
    assert len(data) == 1
    assert data[0]["sub_id"] == str(sub)

    data = _req({"sub_id": str(user_id)})
    assert len(data) == 0


def test_create_person_does_not_accept_sub_id(client, json_data):
    sub = str(uuid.uuid4())
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data | {"sub_id": sub},
    ).json()
    # sub_id in the payload is ignored; it can only be set programmatically
    assert data["sub_id"] is None
