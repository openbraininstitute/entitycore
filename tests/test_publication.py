import pytest

from app.db.model import Publication

from .utils import (
    USER_SUB_ID_1,
    add_db,
    assert_request,
    check_global_delete_one,
    check_global_read_one,
    check_global_update_one,
    check_missing,
)

ROUTE = "/publication"
ADMIN_ROUTE = "/admin/publication"


@pytest.fixture
def json_data(publication_json_data):
    return publication_json_data


def _assert_read_response(data, json_data):
    assert data["DOI"] == json_data["DOI"]
    assert data["title"] == json_data["title"]
    assert data["authors"] == json_data["authors"]
    assert data["publication_year"] == json_data["publication_year"]
    assert data["abstract"] == json_data["abstract"]
    assert data["created_by"]["id"] == data["updated_by"]["id"]


@pytest.fixture
def create_id(client_admin, json_data):
    def _create_id(**kwargs):
        return assert_request(client_admin.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


@pytest.fixture
def model_id(publication):
    return publication.id


def test_create_one(client_admin, json_data):
    data = assert_request(client_admin.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_create_one__doi_validation(client_admin, json_data):
    # should not allow registering a publication without a DOI
    data = assert_request(
        client_admin.post,
        url=ROUTE,
        json={k: v for k, v in json_data.items() if k != "DOI"},
        expected_status_code=422,
    ).json()
    assert data["message"] == "Validation error"

    valid_dois = [
        "10.1080/10509585.2015.1092083",
        "10.1038/s41586-020-2649-2",
        "10.1016/B978-0-12-814141-0.00003-4",
        "10.5061/dryad.q447c/1",
        "10.6028/NIST.SP.800-53r5",
        "10.5281/zenodo.3477281",
        "10.1101/2020.01.01.123456",
    ]

    for doi in valid_dois:
        data = assert_request(client_admin.post, url=ROUTE, json=json_data | {"DOI": doi}).json()
        assert data["DOI"] == doi

    invalid_dois = [
        "10.1000/",
        "11.1038/s41586-020-2649-2",
        "10.1000/abc def",
        "10.1000/abc@def",
    ]

    for doi in invalid_dois:
        data = assert_request(
            client_admin.post, url=ROUTE, json=json_data | {"DOI": doi}, expected_status_code=422
        ).json()
        assert data["message"] == "Validation error"

    # duplicate should not be registered regardless of the case
    doi = "10.5281/ZENODO.3477281"
    data = assert_request(
        client_admin.post, url=ROUTE, json=json_data | {"DOI": doi}, expected_status_code=409
    ).json()
    assert data["error_code"] == "ENTITY_DUPLICATED"


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
            "title": "publication",
            "DOI": "10.1080/10509585.2015.1092083",
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
            Publication: 1,
        },
        expected_counts_after={
            Publication: 0,
        },
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_pagination(client, models):  # noqa: ARG001
    data = assert_request(client.get, url=ROUTE, params={"page_size": 2}).json()
    assert "facets" in data
    assert "data" in data
    assert data["facets"] is None
    assert len(data["data"]) == 2


@pytest.fixture
def models(db, json_data, person_id):
    res = []
    for i in range(5):
        row = add_db(
            db,
            Publication(
                **json_data
                | {
                    "title": f"t{i}",
                    "DOI": f"doi-{i}",
                    "publication_year": 2020 + i,
                    "created_by_id": person_id,
                    "updated_by_id": person_id,
                }
            ),
        )
        res.append(row)

    return res


def test_filtering_sorting(client, models):
    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    data = req({"publication_year__gte": 2020})
    assert len(data) == len(models)

    data = req({"publication_year__in": [2021, 2024]})
    assert {d["publication_year"] for d in data} == {2021, 2024}

    data = req({"publication_year__in": [2021, 2024], "order_by": "publication_year"})
    assert [d["publication_year"] for d in data] == [2021, 2024]

    data = req({"publication_year__in": [2021, 2024], "order_by": "-publication_year"})
    assert [d["publication_year"] for d in data] == [2024, 2021]

    data = req({"publication_year__lte": 2022, "order_by": "title"})
    assert [d["publication_year"] for d in data] == [2020, 2021, 2022]

    data = req({"publication_year__lte": 2022, "order_by": "-title"})
    assert [d["publication_year"] for d in data] == [2022, 2021, 2020]

    data = req({"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1})
    assert len(data) == len(models)
