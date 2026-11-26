import hashlib

import pytest

from app.db.model import Derivation, ResearchLog
from app.db.types import AssetLabel, ContentType, DerivationType, EntityType

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


def _upload_document(client, model, content: bytes = b"# Log\n") -> dict:
    return upload_entity_asset(
        client,
        entity_type=EntityType.research_log,
        entity_id=model.id,
        files={"file": ("log.md", content, "text/markdown")},
        label=AssetLabel.research_log_document,
    ).json()


def _replace(client, url: str, content: bytes, if_match: str | None, expected: int = 200):
    return assert_request(
        client.put,
        url=url,
        files={"file": ("log.md", content, "text/markdown")},
        headers={} if if_match is None else {"If-Match": if_match},
        expected_status_code=expected,
    )


def test_replace_document(clients, model, s3, s3_internal_bucket):
    first = _upload_document(clients.user_1, model)
    url = f"{ADMIN_ROUTE}/{model.id}/assets/{first['id']}"
    new_content = b"# Log\n\nResting potential **-68 mV**.\n"

    response = _replace(clients.admin, url, new_content, f'"{first["sha256_digest"]}"')
    replaced = response.json()
    assert replaced["id"] == first["id"]
    assert replaced["path"] == first["path"]
    assert replaced["full_path"] == first["full_path"]
    assert replaced["size"] == len(new_content)
    assert replaced["sha256_digest"] == hashlib.sha256(new_content).hexdigest()
    assert response.headers["ETag"] == f'"{replaced["sha256_digest"]}"'
    head = s3.head_object(Bucket=s3_internal_bucket, Key=first["full_path"])
    assert head["ContentType"] == "text/markdown"
    body = s3.get_object(Bucket=s3_internal_bucket, Key=first["full_path"])["Body"].read()
    assert body == new_content
    saved = assert_request(clients.admin.get, url=url).json()
    assert saved["sha256_digest"] == replaced["sha256_digest"]

    error = assert_request(
        clients.admin.put,
        url=url,
        files={"file": ("log.json", b"{}", "application/json")},
        headers={"If-Match": replaced["sha256_digest"]},
        expected_status_code=422,
    ).json()
    assert error["error_code"] == "ASSET_INVALID_CONTENT_TYPE"

    folder = assert_request(
        clients.user_1.post,
        url=f"{ROUTE}/{model.id}/assets/directory/upload",
        json={
            "files": ["a.png"],
            "meta": None,
            "label": AssetLabel.research_log_files,
            "directory_name": "files",
        },
    ).json()["asset"]
    error = _replace(
        clients.admin, f"{ADMIN_ROUTE}/{model.id}/assets/{folder['id']}", new_content, None, 409
    ).json()
    assert error["error_code"] == "ASSET_NOT_REPLACEABLE"

    _replace(clients.user_1, url, b"x", replaced["sha256_digest"], 403)
    _replace(
        clients.admin,
        f"{ADMIN_ROUTE}/{model.id}/assets/00000000-0000-0000-0000-000000000000",
        b"x",
        replaced["sha256_digest"],
        404,
    )
    body = s3.get_object(Bucket=s3_internal_bucket, Key=first["full_path"])["Body"].read()
    assert body == new_content


def test_replace_document_needs_the_version_read(clients, model, s3, s3_internal_bucket):
    first = _upload_document(clients.user_1, model)
    url = f"{ADMIN_ROUTE}/{model.id}/assets/{first['id']}"

    alice = _replace(clients.admin, url, b"# Log\n\nAlice\n", first["sha256_digest"]).json()
    error = _replace(clients.admin, url, b"# Log\n\nBob\n", first["sha256_digest"], 412).json()
    assert error["error_code"] == "ASSET_VERSION_MISMATCH"
    assert error["details"] == {"sha256_digest": alice["sha256_digest"]}
    body = s3.get_object(Bucket=s3_internal_bucket, Key=first["full_path"])["Body"].read()
    assert body == b"# Log\n\nAlice\n"

    assert _replace(clients.admin, url, b"x", None, 428).json()["error_code"] == "INVALID_REQUEST"
    for bad in [f'W/"{alice["sha256_digest"]}"', "*", f"{alice['sha256_digest']}, abc", "abc"]:
        assert _replace(clients.admin, url, b"x", bad, 422).json()["error_code"] == (
            "INVALID_REQUEST"
        )
    saved = assert_request(clients.admin.get, url=url).json()
    assert saved["sha256_digest"] == alice["sha256_digest"]


def test_replace_document_refuses_an_empty_file(clients, model, s3, s3_internal_bucket):
    first = _upload_document(clients.user_1, model)
    url = f"{ADMIN_ROUTE}/{model.id}/assets/{first['id']}"

    error = _replace(clients.admin, url, b"", first["sha256_digest"], 422).json()

    assert error["error_code"] == "ASSET_INVALID_FILE"
    body = s3.get_object(Bucket=s3_internal_bucket, Key=first["full_path"])["Body"].read()
    assert body == b"# Log\n"


def test_replace_document_of_a_public_log(db, clients, model, s3, s3_internal_bucket):
    first = _upload_document(clients.user_1, model)
    url = f"{ADMIN_ROUTE}/{model.id}/assets/{first['id']}"
    model.authorized_public = True
    db.commit()

    error = _replace(clients.admin, url, b"# changed\n", first["sha256_digest"], 403).json()

    assert error["error_code"] == "ENTITY_FORBIDDEN"
    body = s3.get_object(Bucket=s3_internal_bucket, Key=first["full_path"])["Body"].read()
    assert body == b"# Log\n"


def test_replace_document_heals_after_a_failed_transaction(
    clients, model, s3, s3_internal_bucket, monkeypatch
):
    first = _upload_document(clients.user_1, model, b"# old\n")
    url = f"{ADMIN_ROUTE}/{model.id}/assets/{first['id']}"
    key = first["full_path"]

    def fail_after_the_s3_write(*_args, **_kwargs):
        msg = "database down"
        raise RuntimeError(msg)

    with monkeypatch.context() as patched:
        patched.setattr("app.service.asset.get_or_create_user", fail_after_the_s3_write)
        with pytest.raises(RuntimeError, match="database down"):
            _replace(clients.admin, url, b"# new\n", first["sha256_digest"])
    assert s3.get_object(Bucket=s3_internal_bucket, Key=key)["Body"].read() == b"# new\n"
    saved = assert_request(clients.admin.get, url=url).json()
    assert saved["sha256_digest"] == first["sha256_digest"]

    replaced = _replace(clients.admin, url, b"# newer\n", first["sha256_digest"]).json()
    assert replaced["sha256_digest"] == hashlib.sha256(b"# newer\n").hexdigest()
    assert s3.get_object(Bucket=s3_internal_bucket, Key=key)["Body"].read() == b"# newer\n"


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
