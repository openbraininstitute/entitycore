import base64
import hashlib
import urllib.parse

import pytest
import requests

from app.db.model import Derivation, ResearchLog
from app.db.types import AssetLabel, ContentType, DerivationType, EntityType
from app.schemas.asset import DIRECTORY_ADD_FILES_MAX

from .utils import (
    assert_request,
    check_admin_create_one,
    check_authorization,
    check_creation_fields,
    check_entity_delete_one,
    check_entity_read_many,
    check_entity_update_one,
    check_missing,
    check_pagination,
    count_db_class,
    upload_entity_asset,
)

ROUTE = "research-log"
ADMIN_ROUTE = "/admin/research-log"


@pytest.fixture
def json_data(research_log_json_data):
    return research_log_json_data


@pytest.fixture
def model(research_log):
    return research_log


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


def _assert_read_response(data, json_data):
    assert "id" in data
    assert "authorized_public" in data
    assert "authorized_project_id" in data
    assert "assets" in data
    assert data["name"] == json_data["name"]
    assert data["description"] == json_data["description"]
    assert data["type"] == EntityType.research_log

    check_creation_fields(data)


def _create_derivation(client, *, used_id, generated_id, derivation_type):
    return assert_request(
        client.post,
        url="/derivation",
        json={
            "used_id": str(used_id),
            "generated_id": str(generated_id),
            "derivation_type": derivation_type,
        },
    ).json()


def test_update_one(clients, json_data):
    check_entity_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        patch_payload={
            "name": "name",
            "description": "description",
        },
        optional_payload=None,
    )


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_admin_create_one(db, clients, json_data, mock_virtual_lab_api):
    check_admin_create_one(
        db=db,
        clients=clients,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        json_data=json_data,
        mock_virtual_lab_api=mock_virtual_lab_api,
    )


def test_user_read_one(client, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_admin_read_one(client_admin, model, json_data):
    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_read_many(client, model, json_data):
    data = assert_request(client.get, url=ROUTE).json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == str(model.id)
    _assert_read_response(data[0], json_data)


def test_read_many_search(client, create_id):
    research_log_id = create_id(name="spines analysis", description="spine density per layer")
    create_id(name="other", description="connectivity")

    data = assert_request(client.get, url=ROUTE, params={"search": "spine"}).json()["data"]
    assert [d["id"] for d in data] == [research_log_id]


def test_read_many_check(clients, json_data):
    check_entity_read_many(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
    )


def test_delete_one(db, clients, json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        expected_counts_before={ResearchLog: 1},
        expected_counts_after={ResearchLog: 0},
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, json_data):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


def test_upload_document(client, model):
    response = upload_entity_asset(
        client,
        entity_type=EntityType.research_log,
        entity_id=model.id,
        files={"file": ("log.md", b"# Research log\n", "text/markdown")},
        label=AssetLabel.research_log_document,
    )
    data = response.json()
    assert data["label"] == AssetLabel.research_log_document
    assert data["content_type"] == ContentType.markdown
    assert data["path"] == "log.md"


def test_upload_document_with_invalid_content_type(client, model):
    response = upload_entity_asset(
        client,
        entity_type=EntityType.research_log,
        entity_id=model.id,
        files={"file": ("log.txt", b"Research log", "text/plain")},
        label=AssetLabel.research_log_document,
        expected_status=422,
    )
    assert response.json()["error_code"] == "ASSET_INVALID_SCHEMA"


def test_upload_files_directory(client, model):
    data = assert_request(
        client.post,
        url=f"{ROUTE}/{model.id}/assets/directory/upload",
        json={
            "files": ["figures/fig1.png", "data/table.csv"],
            "meta": None,
            "label": AssetLabel.research_log_files,
            "directory_name": "files",
        },
    ).json()
    assert data["asset"]["is_directory"] is True
    assert data["asset"]["label"] == AssetLabel.research_log_files
    assert set(data["files"]) == {"figures/fig1.png", "data/table.csv"}


def _files_directory(client, model) -> dict:
    return assert_request(
        client.post,
        url=f"{ROUTE}/{model.id}/assets/directory/upload",
        json={
            "files": ["figures/fig1.png"],
            "meta": None,
            "label": AssetLabel.research_log_files,
            "directory_name": "files",
        },
    ).json()["asset"]


def _file(path: str, content: bytes = b"x") -> dict:
    return {
        "path": path,
        "size": len(content),
        "sha256_digest": hashlib.sha256(content).hexdigest(),
    }


def test_add_files_to_directory(clients, model, s3, s3_internal_bucket):
    client = clients.user_1
    directory = _files_directory(client, model)
    s3.put_object(
        Bucket=s3_internal_bucket, Key=f"{directory['full_path']}/figures/fig1.png", Body=b"png"
    )
    add_url = f"{ROUTE}/{model.id}/assets/{directory['id']}/directory/files"

    data = assert_request(
        client.post,
        url=add_url,
        json={"files": [_file("figures/fig2.png"), _file("results/rates.csv")]},
    ).json()
    assert data["asset"]["id"] == directory["id"]
    assert set(data["files"]) == {"figures/fig2.png", "results/rates.csv"}
    assert f"{directory['full_path']}/results/rates.csv" in data["files"]["results/rates.csv"]

    s3.put_object(
        Bucket=s3_internal_bucket, Key=f"{directory['full_path']}/results/rates.csv", Body=b"a,b"
    )
    listed = assert_request(client.get, url=f"{ROUTE}/{model.id}/assets/{directory['id']}/list")
    assert set(listed.json()["files"]) == {"figures/fig1.png", "results/rates.csv"}

    error = assert_request(
        client.post,
        url=add_url,
        json={"files": [_file("figures/fig3.png"), _file("figures/fig1.png")]},
        expected_status_code=409,
    ).json()
    assert error["error_code"] == "ASSET_DIRECTORY_FILE_DUPLICATED"
    assert error["details"] == {"existing": ["figures/fig1.png"]}

    document = upload_entity_asset(
        client,
        entity_type=EntityType.research_log,
        entity_id=model.id,
        files={"file": ("log.md", b"# Research log\n", "text/markdown")},
        label=AssetLabel.research_log_document,
    ).json()
    error = assert_request(
        client.post,
        url=f"{ROUTE}/{model.id}/assets/{document['id']}/directory/files",
        json={"files": [_file("x.png")]},
        expected_status_code=422,
    ).json()
    assert error["error_code"] == "ASSET_NOT_A_DIRECTORY"

    assert_request(
        clients.user_2.post, url=add_url, json={"files": [_file("x.png")]}, expected_status_code=404
    )


def test_add_files_upload_is_enforced_by_s3(client, model, s3, s3_internal_bucket):
    directory = _files_directory(client, model)
    add_url = f"{ROUTE}/{model.id}/assets/{directory['id']}/directory/files"
    content = b"\x89PNG plot"
    file = _file("figures/rate.png", content)

    data = assert_request(client.post, url=add_url, json={"files": [file]}).json()
    checksum = base64.b64encode(bytes.fromhex(file["sha256_digest"])).decode()
    assert data["headers"] == {
        "figures/rate.png": {
            "If-None-Match": "*",
            "Content-Length": str(len(content)),
            "x-amz-checksum-sha256": checksum,
        }
    }
    signed = urllib.parse.parse_qs(urllib.parse.urlparse(data["files"]["figures/rate.png"]).query)
    assert signed["X-Amz-SignedHeaders"] == [
        "content-length;host;if-none-match;x-amz-checksum-sha256"
    ]
    assert signed["X-Amz-Expires"] == ["900"]

    url, headers = data["files"]["figures/rate.png"], data["headers"]["figures/rate.png"]
    assert requests.put(url, data=content, headers=headers, timeout=10).status_code == 200
    again = requests.put(url, data=content, headers=headers, timeout=10)
    assert again.status_code == 412
    key = f"{directory['full_path']}/figures/rate.png"
    assert s3.get_object(Bucket=s3_internal_bucket, Key=key)["Body"].read() == content

    error = assert_request(
        client.post, url=add_url, json={"files": [file]}, expected_status_code=409
    ).json()
    assert error["details"] == {"existing": ["figures/rate.png"]}

    for files in [
        [_file("a.png"), _file("a.png", b"y")],
        ["a.png"],
        [{**_file("a.png"), "sha256_digest": "abc"}],
        [{**_file("a.png"), "size": -1}],
        [_file(f"f{i}.png") for i in range(DIRECTORY_ADD_FILES_MAX + 1)],
    ]:
        assert_request(client.post, url=add_url, json={"files": files}, expected_status_code=422)


def test_add_files_to_open_storage_directory(client, model, s3, s3_open_bucket):
    s3.put_object(Bucket=s3_open_bucket, Key="open/data/a.csv", Body=b"a")
    directory = assert_request(
        client.post,
        url=f"{ROUTE}/{model.id}/assets/register",
        json={
            "path": "files",
            "full_path": "open/data",
            "is_directory": True,
            "content_type": "application/vnd.directory",
            "label": AssetLabel.research_log_files,
            "storage_type": "aws_s3_open",
        },
        expected_status_code=201,
    ).json()
    error = assert_request(
        client.post,
        url=f"{ROUTE}/{model.id}/assets/{directory['id']}/directory/files",
        json={"files": [_file("b.csv")]},
        expected_status_code=409,
    ).json()
    assert error["error_code"] == "ASSET_INVALID_PATH"


def test_derivations(db, client, model, root_circuit, circuit):
    # root_circuit is a public input, circuit is a private output of the same project
    _create_derivation(
        client,
        used_id=root_circuit.id,
        generated_id=model.id,
        derivation_type=DerivationType.research_log_input,
    )
    _create_derivation(
        client,
        used_id=circuit.id,
        generated_id=model.id,
        derivation_type=DerivationType.research_log_output,
    )

    def _linked_ids(url, expand):
        data = assert_request(client.get, url=url, params={"expand": expand}).json()
        direction, _, _ = expand.partition(":")
        side = "used" if direction == "generated_from_derivations" else "generated"
        return [d[side]["id"] for d in data[direction]]

    # from the ResearchLog
    url = f"{ROUTE}/{model.id}"
    assert _linked_ids(url, "generated_from_derivations:research_log_input") == [
        str(root_circuit.id)
    ]
    assert _linked_ids(url, "generated_from_derivations:research_log_output") == [str(circuit.id)]

    # from the linked entities
    assert _linked_ids(f"/circuit/{root_circuit.id}", "used_by_derivations:research_log_input") == [
        str(model.id)
    ]
    assert _linked_ids(f"/circuit/{circuit.id}", "used_by_derivations:research_log_output") == [
        str(model.id)
    ]

    # search the ResearchLogs that used an entity
    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "generated_derivation__used_id": str(root_circuit.id),
            "generated_derivation__derivation_type": DerivationType.research_log_input,
        },
    ).json()["data"]
    assert [d["id"] for d in data] == [str(model.id)]

    # deleting the ResearchLog deletes the derivations, but not the linked entities
    assert count_db_class(db, Derivation) == 2
    assert_request(client.delete, url=f"{ROUTE}/{model.id}")
    assert count_db_class(db, Derivation) == 0
    assert_request(client.get, url=f"/circuit/{root_circuit.id}")
    assert_request(client.get, url=f"/circuit/{circuit.id}")


@pytest.mark.parametrize(
    "derivation_type", [DerivationType.research_log_input, DerivationType.research_log_output]
)
def test_derivation_generated_must_be_research_log(client, model, circuit, derivation_type):
    data = assert_request(
        client.post,
        url="/derivation",
        json={
            "used_id": str(model.id),
            "generated_id": str(circuit.id),
            "derivation_type": derivation_type,
        },
        expected_status_code=422,
    ).json()
    assert data["error_code"] == "INVALID_REQUEST"
    assert "requires generated entity type" in data["details"][0]
