import functools
from pathlib import Path

from httpx import Headers
from starlette.testclient import TestClient

from app.db.types import EntityType

TEST_DATA_DIR = Path(__file__).parent / "data"

TOKEN_ADMIN = "I'm admin"  # noqa: S105
TOKEN_USER_1 = "I'm user 1"  # noqa: S105
TOKEN_USER_2 = "I'm user 2"  # noqa: S105

AUTH_HEADER_ADMIN = {"Authorization": f"Bearer {TOKEN_ADMIN}"}
AUTH_HEADER_USER_1 = {"Authorization": f"Bearer {TOKEN_USER_1}"}
AUTH_HEADER_USER_2 = {"Authorization": f"Bearer {TOKEN_USER_2}"}

VIRTUAL_LAB_ID = "9c6fba01-2c6f-4eac-893f-f0dc665605c5"
PROJECT_ID = "ee86d4a0-eaca-48ca-9788-ddc450250b15"
UNRELATED_VIRTUAL_LAB_ID = "99999999-2c6f-4eac-893f-f0dc665605c5"
UNRELATED_PROJECT_ID = "66666666-eaca-48ca-9788-ddc450250b15"

MISSING_ID = "12345678-1234-5678-1234-567812345678"
MISSING_ID_COMPACT = MISSING_ID.replace("-", "")

PROJECT_HEADERS = {
    "virtual-lab-id": VIRTUAL_LAB_ID,
    "project-id": PROJECT_ID,
}
UNRELATED_PROJECT_HEADERS = {
    "virtual-lab-id": UNRELATED_VIRTUAL_LAB_ID,
    "project-id": UNRELATED_PROJECT_ID,
}


class ClientProxy:
    """Proxy TestClient to pass default headers without creating a new instance.

    This can be used to avoid running the lifespan event multiple times.
    """

    def __init__(self, client: TestClient, headers: dict | None = None) -> None:
        self._client = client
        self._headers = headers
        self._methods = {"request", "get", "options", "head", "post", "put", "patch", "delete"}

    def __getattr__(self, name: str):
        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args, headers=None, **kwargs):
                merged_headers = Headers(self._headers)
                merged_headers.update(headers)
                return f(*args, headers=merged_headers, **kwargs)

            return wrapper

        method = getattr(self._client, name)
        return decorator(method) if name in self._methods else method


def create_reconstruction_morphology_id(
    client,
    species_id,
    strain_id,
    brain_region_id,
    authorized_public,
    name="Test Morphology Name",
    description="Test Morphology Description",
):
    response = client.post(
        "/reconstruction-morphology",
        json={
            "name": name,
            "description": description,
            "brain_region_id": str(brain_region_id) if isinstance(brain_region_id, int) else None,
            "species_id": str(species_id) if species_id else None,
            "strain_id": str(strain_id) if strain_id else None,
            "location": {"x": 10, "y": 20, "z": 30},
            "legacy_id": ["Test Legacy ID"],
            "authorized_public": authorized_public,
        },
    )

    assert response.status_code == 200
    return response.json()["id"]


def add_db(db, row):
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def add_all_db(db, rows):
    db.add_all(rows)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def assert_response(response, expected_status_code=200):
    assert response.status_code == expected_status_code, (
        f"Request {response.request.method} {response.request.url}: "
        f"expected={expected_status_code}, actual={response.status_code}, "
        f"content={response.content}"
    )


def assert_request(client_method, *, expected_status_code=200, **kwargs):
    response = client_method(**kwargs)
    assert_response(response, expected_status_code=expected_status_code)
    return response


def create_brain_region_id(client, id_: int, name: str):
    js = {
        "id": id_,
        "acronym": f"acronym{id_}",
        "name": name,
        "color_hex_triplet": "FF0000",
        "children": [],
    }
    response = assert_request(
        client.post,
        url="/brain-region",
        json=js,
    )
    data = response.json()
    assert "id" in data, f"Failed to get id for brain region: {data}"
    return data["id"]


def check_missing(route, client):
    assert_request(
        client.get,
        url=f"{route}/{MISSING_ID}",
        expected_status_code=404,
    )
    assert_request(
        client.get,
        url=f"{route}/{MISSING_ID_COMPACT}",
        expected_status_code=404,
    )
    assert_request(
        client.get,
        url=f"{route}/42424242",
        expected_status_code=422,
    )
    assert_request(
        client.get,
        url=f"{route}/notanumber",
        expected_status_code=422,
    )


def check_pagination(route, client, constructor_func):
    for i in range(3):
        constructor_func(
            name=f"name-{i}",
            description=f"description-{i}",
        )

    response = assert_request(
        client.get,
        url=route,
        params={"page_size": 2},
    )
    response_json = response.json()
    assert "facets" in response_json
    assert "data" in response_json
    assert response_json["facets"] is None
    assert len(response_json["data"]) == 2


def check_authorization(route, client_user_1, client_user_2, client_no_project, json_data):
    response = assert_request(
        client_user_1.post,
        url=route,
        json=json_data
        | {
            "name": "Public Entity",
            "authorized_public": True,
        },
    )
    public_morph = response.json()

    inaccessible_obj = assert_request(
        client_user_2.post,
        url=route,
        json=json_data | {"name": "inaccessible morphology 1"},
    )
    inaccessible_obj = inaccessible_obj.json()

    private_obj0 = assert_request(
        client_user_1.post,
        url=route,
        json=json_data | {"name": "private morphology 0"},
    )
    private_obj0 = private_obj0.json()

    private_obj1 = assert_request(
        client_user_1.post,
        url=route,
        json=json_data
        | {
            "name": "private morphology 1",
        },
    )
    private_obj1 = private_obj1.json()

    # only return results that matches the desired project, and public ones
    response = assert_request(
        client_user_1.get,
        url=route,
    )
    data = response.json()["data"]

    ids = {row["id"] for row in data}
    expected = {
        public_morph["id"],
        private_obj0["id"],
        private_obj1["id"],
    }
    assert ids == expected, (
        "Failed to fetch project-specific and public ids.\n"
        f"Expected: {sorted(expected)}\n"
        f"Actual  : {sorted(ids)}"
    )

    assert_request(
        client_user_1.get,
        url=f"{route}/{inaccessible_obj['id']}",
        expected_status_code=404,
    )

    # only returns public results
    response = assert_request(
        client_no_project.get,
        url=route,
    )
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == public_morph["id"]


def create_asset_file(client, entity_type, entity_id, file_name, file_obj):
    route = EntityType[entity_type].replace("_", "-")
    files = {
        # (filename, file (or bytes), content_type, headers)
        "file": (str(file_name), file_obj, "text/plain")
    }
    assert_request(
        client.post,
        url=f"{route}/{entity_id}/assets",
        files=files,
        expected_status_code=201,
    )
