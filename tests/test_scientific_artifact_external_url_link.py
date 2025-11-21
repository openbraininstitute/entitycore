import pytest

from app.db.model import ScientificArtifactExternalUrlLink

from .utils import (
    USER_SUB_ID_1,
    add_all_db,
    assert_request,
    check_missing,
)

ROUTE = "/scientific-artifact-external-url-link"
ADMIN_ROUTE = "/admin/scientific-artifact-external-url-link"


@pytest.fixture
def json_data(external_url, root_circuit):
    return {
        "external_url_id": str(external_url.id),
        "scientific_artifact_id": str(root_circuit.id),
    }


def _assert_read_response(data, json_data):
    assert "id" in data
    assert data["external_url"]["id"] == json_data["external_url_id"]
    assert data["scientific_artifact"]["id"] == json_data["scientific_artifact_id"]
    assert data["created_by"]["id"] == data["updated_by"]["id"]


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


@pytest.fixture
def model_id(create_id):
    return create_id()


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_user_read_one(client, model_id, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model_id}").json()
    _assert_read_response(data, json_data)


def test_admin_read_one(client_admin, model_id, json_data):
    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{model_id}").json()
    _assert_read_response(data, json_data)


def test_read_many(client, model_id, json_data):
    data = assert_request(client.get, url=ROUTE).json()
    assert len(data["data"]) == 1
    _assert_read_response(data["data"][0], json_data)
    assert data["data"][0]["id"] == str(model_id)


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(
    client_user_1,
    client_user_2,
    json_data,
    root_circuit_json_data,
    external_url,
):
    circuit_json_data = root_circuit_json_data | {"authorized_public": False}
    circuit_1 = assert_request(
        client_user_1.post,
        url="/circuit",
        json=circuit_json_data,
    ).json()
    circuit_2 = assert_request(
        client_user_2.post,
        url="/circuit",
        json=circuit_json_data,
    ).json()

    # user 1 creates link between accessible entities
    data = assert_request(
        client_user_1.post,
        url=ROUTE,
        json=json_data
        | {
            "external_url_id": str(external_url.id),
            "scientific_artifact_id": circuit_1["id"],
        },
    ).json()
    assert data["id"]

    # user 1 fetches successfully accessible links
    data = assert_request(client_user_1.get, url=ROUTE).json()["data"]
    assert len(data) == 1

    # user 1 creates link between external_url and inaccessible circuit
    data = assert_request(
        client_user_1.post,
        url=ROUTE,
        json=json_data
        | {
            "external_url_id": str(external_url.id),
            "scientific_artifact_id": circuit_2["id"],
        },
        expected_status_code=404,
    ).json()

    # user 2 creates link between external_url and inaccessible circuit
    data = assert_request(
        client_user_2.post,
        url=ROUTE,
        json=json_data
        | {
            "external_url_id": str(external_url.id),
            "scientific_artifact_id": circuit_2["id"],
        },
    ).json()

    # user 1 fetched only the accessible link
    data = assert_request(client_user_1.get, url=ROUTE).json()["data"]
    assert len(data) == 1
    assert data[0]["scientific_artifact"]["id"] == circuit_1["id"]

    # user 2 fetched only the accessible link
    data = assert_request(client_user_2.get, url=ROUTE).json()["data"]
    assert len(data) == 1
    assert data[0]["scientific_artifact"]["id"] == circuit_2["id"]


@pytest.fixture
def models(db, json_data, person_id, external_url, root_circuit, circuit):
    results = add_all_db(
        db,
        [
            ScientificArtifactExternalUrlLink(
                **json_data
                | {
                    "external_url_id": external_url.id,
                    "scientific_artifact_id": root_circuit.id,
                    "created_by_id": person_id,
                    "updated_by_id": person_id,
                }
            ),
            ScientificArtifactExternalUrlLink(
                **json_data
                | {
                    "external_url_id": external_url.id,
                    "scientific_artifact_id": circuit.id,
                    "created_by_id": person_id,
                    "updated_by_id": person_id,
                }
            ),
        ],
    )

    return results


def test_pagination(client, models):
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"page_size": 1},
    ).json()
    assert "facets" in data
    assert "data" in data
    assert data["facets"] is None
    assert len(data["data"]) == 1

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"page_size": len(models)},
    ).json()
    assert len(data["data"]) == len(models)


def test_filtering_sorting(client, models, external_url, root_circuit):
    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    data = req({"order_by": "creation_date"})
    assert len(data) == len(models)

    data = req({"external_url__id": str(external_url.id)})
    assert len(data) == len(models)

    data = req({"scientific_artifact__id": str(root_circuit.id)})
    assert len(data) == 1
    assert data[0]["scientific_artifact"]["id"] == str(root_circuit.id)

    data = req({"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1})
    assert len(data) == len(models)
