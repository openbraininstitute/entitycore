import base64
import datetime as dt
import hashlib
import time
import urllib.parse

import boto3
import pytest
import requests
import sqlalchemy as sa
from botocore.client import Config
from sqlalchemy.orm import Session

from app.config import settings
from app.db.events import StorageUndo, undo_storage_write_unless_committed
from app.db.model import Derivation, Entity, ResearchLog
from app.db.types import AssetLabel, ContentType, DerivationType, EntityType, StorageType
from app.schemas.asset import DIRECTORY_ADD_FILES_MAX
from app.service import asset as asset_service
from app.utils.s3 import _apply_presigned_url_netloc

from .utils import (
    assert_request,
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


def test_add_files_to_directory(clients, model, s3, s3_internal_bucket):
    """A research log's files folder grows over time; an existing file is never replaced."""
    client = clients.user_1
    created = assert_request(
        client.post,
        url=f"{ROUTE}/{model.id}/assets/directory/upload",
        json={
            "files": ["figures/fig1.png"],
            "meta": None,
            "label": AssetLabel.research_log_files,
            "directory_name": "files",
        },
    ).json()
    directory = created["asset"]
    s3.put_object(
        Bucket=s3_internal_bucket, Key=f"{directory['full_path']}/figures/fig1.png", Body=b"png"
    )
    add_url = f"{ROUTE}/{model.id}/assets/{directory['id']}/directory/files"

    # new files: one presigned url each, inside the same directory
    data = assert_request(
        client.post, url=add_url, json={"files": ["figures/fig2.png", "results/rates.csv"]}
    ).json()
    assert data["asset"]["id"] == directory["id"]
    assert set(data["files"]) == {"figures/fig2.png", "results/rates.csv"}
    assert f"{directory['full_path']}/results/rates.csv" in data["files"]["results/rates.csv"]

    # once uploaded, an added file is listed with the others
    s3.put_object(
        Bucket=s3_internal_bucket, Key=f"{directory['full_path']}/results/rates.csv", Body=b"a,b"
    )
    listed = assert_request(client.get, url=f"{ROUTE}/{model.id}/assets/{directory['id']}/list")
    assert set(listed.json()["files"]) == {"figures/fig1.png", "results/rates.csv"}

    # an existing file is refused, and nothing is signed for the rest of the request
    error = assert_request(
        client.post,
        url=add_url,
        json={"files": ["figures/fig3.png", "figures/fig1.png"]},
        expected_status_code=409,
    ).json()
    assert error["error_code"] == "ASSET_DUPLICATED"
    assert error["details"] == {"existing": ["figures/fig1.png"]}

    # the same file twice in one request
    assert_request(
        client.post, url=add_url, json={"files": ["a.png", "a.png"]}, expected_status_code=422
    )

    # a file that is not a directory
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
        json={"files": ["x.png"]},
        expected_status_code=422,
    ).json()
    assert error["error_code"] == "ASSET_NOT_A_DIRECTORY"

    # a user of another project cannot add files
    assert_request(
        clients.user_2.post, url=add_url, json={"files": ["x.png"]}, expected_status_code=404
    )


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


def test_add_files_signed(clients, model, s3, s3_internal_bucket):
    """A file sent with size and sha256: S3 accepts it once, and only with those bytes."""
    client = clients.user_1
    directory = _files_directory(client, model)
    add_url = f"{ROUTE}/{model.id}/assets/{directory['id']}/directory/files"
    content = b"\x89PNG plot"
    digest = hashlib.sha256(content).hexdigest()

    data = assert_request(
        client.post,
        url=add_url,
        json={
            "files": [
                {"path": "figures/rate.png", "size": len(content), "sha256_digest": digest},
                "notes.txt",  # a bare path is still accepted, with no check
            ]
        },
    ).json()
    checksum = base64.b64encode(bytes.fromhex(digest)).decode()
    assert data["headers"] == {
        "figures/rate.png": {
            "If-None-Match": "*",
            "Content-Length": str(len(content)),
            "x-amz-checksum-sha256": checksum,
        }
    }
    # SigV4 even though the service's client signs with SigV2: the headers are signed
    signed = urllib.parse.parse_qs(urllib.parse.urlparse(data["files"]["figures/rate.png"]).query)
    assert signed["X-Amz-SignedHeaders"] == [
        "content-length;host;if-none-match;x-amz-checksum-sha256"
    ]
    assert signed["X-Amz-Expires"] == ["900"]
    # a bare path gets the usual URL, but it also lasts only 15 minutes
    bare = urllib.parse.parse_qs(urllib.parse.urlparse(data["files"]["notes.txt"]).query)
    if "Expires" in bare:  # SigV2: an absolute time
        assert 0 < int(bare["Expires"][0]) - time.time() <= 900
    else:
        assert bare["X-Amz-Expires"] == ["900"]
    assert "notes.txt" not in data["headers"]

    # the upload with the headers works; reusing the URL is refused, so a file is never replaced
    url, headers = data["files"]["figures/rate.png"], data["headers"]["figures/rate.png"]
    assert requests.put(url, data=content, headers=headers, timeout=10).status_code == 200
    again = requests.put(url, data=b"other bytes", headers=headers, timeout=10)
    assert again.status_code == 412
    key = f"{directory['full_path']}/figures/rate.png"
    assert s3.get_object(Bucket=s3_internal_bucket, Key=key)["Body"].read() == content

    # now it exists: 409 before any upload, for both the bare and the signed form
    for file in [
        "figures/rate.png",
        {"path": "figures/rate.png", "size": 1, "sha256_digest": digest},
    ]:
        error = assert_request(
            client.post, url=add_url, json={"files": [file]}, expected_status_code=409
        ).json()
        assert error["details"] == {"existing": ["figures/rate.png"]}

    # the same path twice in one request (either form), or a bad digest or size: 422
    for files in [
        ["a.png", {"path": "a.png", "size": 1, "sha256_digest": digest}],
        [{"path": "a.png", "size": 1, "sha256_digest": "abc"}],
        [{"path": "a.png", "size": -1, "sha256_digest": digest}],
        [f"f{i}.png" for i in range(DIRECTORY_ADD_FILES_MAX + 1)],
    ]:
        assert_request(client.post, url=add_url, json={"files": files}, expected_status_code=422)


def test_add_files_to_open_storage_directory(client, model, s3, s3_open_bucket):
    """A directory registered in open storage can't sign uploads: refused, no URL."""
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
        json={"files": ["b.csv"]},
        expected_status_code=409,
    ).json()
    assert error["error_code"] == "ASSET_INVALID_PATH"


def test_replace_document(clients, model, s3, s3_internal_bucket):
    """The log document is replaced in place: same id, path and link, newest content."""
    client = clients.user_1
    first = upload_entity_asset(
        client,
        entity_type=EntityType.research_log,
        entity_id=model.id,
        files={"file": ("log.md", b"# Log\n", "text/markdown")},
        label=AssetLabel.research_log_document,
    ).json()
    url = f"{ROUTE}/{model.id}/assets/{first['id']}"
    new_content = b"# Log\n\nResting potential **-68 mV**.\n"

    response = assert_request(
        client.put,
        url=url,
        files={"file": ("log.md", new_content, "text/markdown")},
        headers={"If-Match": f'"{first["sha256_digest"]}"'},
    )
    replaced = response.json()
    assert replaced["id"] == first["id"]
    assert replaced["path"] == first["path"]
    assert replaced["full_path"] == first["full_path"]
    assert replaced["size"] == len(new_content)
    assert replaced["sha256_digest"] == hashlib.sha256(new_content).hexdigest()
    assert response.headers["ETag"] == f'"{replaced["sha256_digest"]}"'
    body = s3.get_object(Bucket=s3_internal_bucket, Key=first["full_path"])["Body"].read()
    assert body == new_content
    # the row is saved, not only the response
    assert assert_request(client.get, url=url).json()["sha256_digest"] == replaced["sha256_digest"]

    # another content type is refused
    error = assert_request(
        client.put,
        url=url,
        files={"file": ("log.json", b"{}", "application/json")},
        headers={"If-Match": replaced["sha256_digest"]},
        expected_status_code=422,
    ).json()
    assert error["error_code"] == "ASSET_INVALID_CONTENT_TYPE"

    # the files folder is a directory, never replaced
    folder = assert_request(
        client.post,
        url=f"{ROUTE}/{model.id}/assets/directory/upload",
        json={
            "files": ["a.png"],
            "meta": None,
            "label": AssetLabel.research_log_files,
            "directory_name": "files",
        },
    ).json()["asset"]
    error = assert_request(
        client.put,
        url=f"{ROUTE}/{model.id}/assets/{folder['id']}",
        files={"file": ("log.md", new_content, "text/markdown")},
        expected_status_code=409,
    ).json()
    assert error["error_code"] == "ASSET_NOT_REPLACEABLE"

    # a user of another project cannot replace it
    assert_request(
        clients.user_2.put,
        url=url,
        files={"file": ("log.md", b"x", "text/markdown")},
        headers={"If-Match": replaced["sha256_digest"]},
        expected_status_code=404,
    )
    body = s3.get_object(Bucket=s3_internal_bucket, Key=first["full_path"])["Body"].read()
    assert body == new_content


def test_replace_document_needs_the_version_read(clients, model, s3, s3_internal_bucket):
    """Someone who read an older version can't overwrite a newer edit (no lost update)."""
    client = clients.user_1
    first = upload_entity_asset(
        client,
        entity_type=EntityType.research_log,
        entity_id=model.id,
        files={"file": ("log.md", b"# Log\n", "text/markdown")},
        label=AssetLabel.research_log_document,
    ).json()
    url = f"{ROUTE}/{model.id}/assets/{first['id']}"

    def replace(content: bytes, if_match: str | None, expected: int):
        headers = {} if if_match is None else {"If-Match": if_match}
        return assert_request(
            client.put,
            url=url,
            files={"file": ("log.md", content, "text/markdown")},
            headers=headers,
            expected_status_code=expected,
        ).json()

    # Alice and Bob both read the first version; Alice writes first (an unquoted ETag is fine)
    alice = replace(b"# Log\n\nAlice\n", first["sha256_digest"], 200)
    # Bob still sends the version he read: refused, and told which version is current
    error = replace(b"# Log\n\nBob\n", first["sha256_digest"], 412)
    assert error["error_code"] == "ASSET_VERSION_MISMATCH"
    assert error["details"] == {"sha256_digest": alice["sha256_digest"]}
    body = s3.get_object(Bucket=s3_internal_bucket, Key=first["full_path"])["Body"].read()
    assert body == b"# Log\n\nAlice\n"

    # no version: 428; not a sha256 (weak ETag, list, *): 422; nothing gets written
    assert replace(b"x", None, 428)["error_code"] == "INVALID_REQUEST"
    for bad in [f'W/"{alice["sha256_digest"]}"', "*", f"{alice['sha256_digest']}, abc", "abc"]:
        assert replace(b"x", bad, 422)["error_code"] == "INVALID_REQUEST"
    assert assert_request(client.get, url=url).json()["sha256_digest"] == alice["sha256_digest"]


def test_replace_document_of_public_log(db, clients, model):
    """Replacing a published log's content needs delete rights, not just write rights."""
    first = upload_entity_asset(
        clients.user_1,
        entity_type=EntityType.research_log,
        entity_id=model.id,
        files={"file": ("log.md", b"# Log\n", "text/markdown")},
        label=AssetLabel.research_log_document,
    ).json()
    db.execute(sa.update(Entity).where(Entity.id == model.id).values(authorized_public=True))
    db.commit()
    url = f"{ROUTE}/{model.id}/assets/{first['id']}"
    files = {"file": ("log.md", b"# Log\n\nnew\n", "text/markdown")}
    headers = {"If-Match": first["sha256_digest"]}

    # a project admin who isn't a maintainer can't delete a public entity, so can't rewrite it
    error = assert_request(
        clients.user_1.put, url=url, files=files, headers=headers, expected_status_code=403
    ).json()
    assert error["error_code"] == "ENTITY_FORBIDDEN"
    # a maintainer of the project can do both
    assert_request(clients.maintainer_1.put, url=url, files=files, headers=headers)


def _upload_document(client, model, content: bytes = b"# Log\n") -> dict:
    return upload_entity_asset(
        client,
        entity_type=EntityType.research_log,
        entity_id=model.id,
        files={"file": ("log.md", content, "text/markdown")},
        label=AssetLabel.research_log_document,
    ).json()


def _replace(client, url: str, content: bytes, if_match: str, expected: int = 200):
    return assert_request(
        client.put,
        url=url,
        files={"file": ("log.md", content, "text/markdown")},
        headers={"If-Match": if_match},
        expected_status_code=expected,
    )


def test_document_type_is_stored_and_on_the_download_link(client, model, s3, s3_internal_bucket):
    """The object stores its type, and the link answers with it, old objects included."""
    first = _upload_document(client, model)
    key = first["full_path"]
    assert s3.head_object(Bucket=s3_internal_bucket, Key=key)["ContentType"] == "text/markdown"
    replaced = _replace(
        client,
        f"{ROUTE}/{model.id}/assets/{first['id']}",
        b"# Log\n\nnew\n",
        first["sha256_digest"],
    ).json()
    assert s3.head_object(Bucket=s3_internal_bucket, Key=key)["ContentType"] == "text/markdown"
    assert replaced["content_type"] == ContentType.markdown

    # an object stored without a type (like before this change) is served with the row's type
    s3.put_object(Bucket=s3_internal_bucket, Key=key, Body=b"# Log\n")
    link = client.get(
        f"{ROUTE}/{model.id}/assets/{first['id']}/download", follow_redirects=False
    ).headers["location"]
    query = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
    assert query["response-content-type"] == ["text/markdown"]
    # SigV4: newer buckets treat a SigV2 link as anonymous and refuse response-content-type
    assert query["X-Amz-Algorithm"] == ["AWS4-HMAC-SHA256"]
    fetched = requests.get(link, timeout=10)
    assert fetched.headers["Content-Type"] == "text/markdown"

    # a file in a directory: its type comes from its name; an unknown name gets none
    directory = _files_directory(client, model)
    for name, expected in [("figures/fig1.png", ["image/png"]), ("data/run.unknownext", None)]:
        link = client.get(
            f"{ROUTE}/{model.id}/assets/{directory['id']}/download",
            params={"asset_path": name},
            follow_redirects=False,
        ).headers["location"]
        query = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
        assert query.get("response-content-type") == expected


def test_content_changes_move_the_log_date(db, clients, model):
    """Replacing the document or adding files moves the log's update_date and updated_by."""
    client = clients.user_1

    def log_dates():
        row = db.execute(
            sa.select(Entity.update_date, Entity.updated_by_id).where(Entity.id == model.id)
        ).one()
        db.expire_all()
        return row

    first = _upload_document(client, model)
    before = log_dates()
    _replace(client, f"{ROUTE}/{model.id}/assets/{first['id']}", b"# new\n", first["sha256_digest"])
    after_replace = log_dates()
    assert after_replace.update_date > before.update_date

    directory = _files_directory(client, model)
    after_folder = log_dates()
    assert_request(
        client.post,
        url=f"{ROUTE}/{model.id}/assets/{directory['id']}/directory/files",
        json={"files": ["figures/fig2.png"]},
    )
    after_add = log_dates()
    assert after_add.update_date > after_folder.update_date
    assert after_add.updated_by_id == after_replace.updated_by_id is not None

    # a refused request moves nothing
    _replace(client, f"{ROUTE}/{model.id}/assets/{first['id']}", b"x", first["sha256_digest"], 412)
    assert log_dates().update_date == after_add.update_date


def test_admin_replaces_a_document_of_any_project(clients, model, s3, s3_internal_bucket):
    """A service sync has no user: the admin route replaces with the same rules."""
    first = _upload_document(clients.user_1, model)
    url = f"{ADMIN_ROUTE}/{model.id}/assets/{first['id']}"

    response = _replace(clients.admin, url, b"# Log\n\nby the sync\n", first["sha256_digest"])
    replaced = response.json()
    assert response.headers["ETag"] == f'"{replaced["sha256_digest"]}"'
    body = s3.get_object(Bucket=s3_internal_bucket, Key=first["full_path"])["Body"].read()
    assert body == b"# Log\n\nby the sync\n"

    # same rules: the version you read is required and checked
    assert_request(
        clients.admin.put,
        url=url,
        files={"file": ("log.md", b"x", "text/markdown")},
        expected_status_code=428,
    )
    _replace(clients.admin, url, b"x", first["sha256_digest"], 412)
    # only for the admin role, and only for an asset of that entity
    _replace(clients.user_1, url, b"x", replaced["sha256_digest"], 403)
    _replace(
        clients.admin,
        f"{ADMIN_ROUTE}/{model.id}/assets/00000000-0000-0000-0000-000000000000",
        b"x",
        replaced["sha256_digest"],
        404,
    )


def test_replace_puts_s3_back_when_the_transaction_fails(
    clients, model, s3, s3_internal_bucket, monkeypatch
):
    """S3 can't roll back with the database, so the old content is put back (compensation)."""
    client = clients.user_1
    first = _upload_document(client, model, b"# old\n")
    url = f"{ROUTE}/{model.id}/assets/{first['id']}"
    key = first["full_path"]

    def fail_after_the_s3_write(*_args, **_kwargs):
        assert s3.get_object(Bucket=s3_internal_bucket, Key=key)["Body"].read() == b"# new\n"
        msg = "database down"
        raise RuntimeError(msg)

    with monkeypatch.context() as patched:
        patched.setattr("app.service.asset.get_or_create_user", fail_after_the_s3_write)
        with pytest.raises(RuntimeError, match="database down"):
            _replace(client, url, b"# new\n", first["sha256_digest"])
    assert s3.get_object(Bucket=s3_internal_bucket, Key=key)["Body"].read() == b"# old\n"
    head = s3.head_object(Bucket=s3_internal_bucket, Key=key)
    assert head["ContentType"] == "text/markdown"
    # the row rolled back too, so the old version is still the one to send
    assert assert_request(client.get, url=url).json()["sha256_digest"] == first["sha256_digest"]

    # a newer write that came in meanwhile is never overwritten by the undo
    def newer_write_then_fail(*_args, **_kwargs):
        s3.put_object(Bucket=s3_internal_bucket, Key=key, Body=b"# newer\n")
        msg = "database down"
        raise RuntimeError(msg)

    monkeypatch.setattr("app.service.asset.get_or_create_user", newer_write_then_fail)
    with pytest.raises(RuntimeError, match="database down"):
        _replace(client, url, b"# new\n", first["sha256_digest"])
    assert s3.get_object(Bucket=s3_internal_bucket, Key=key)["Body"].read() == b"# newer\n"


def test_storage_undo_runs_only_without_a_commit(db, s3, s3_internal_bucket):
    """Committed: the write stays. Rolled back or closed without commit (failed): undone."""
    key = "private/undo/test.md"

    def write(session: Session, content: bytes) -> None:
        s3.put_object(Bucket=s3_internal_bucket, Key=key, Body=b"# old\n")
        put = s3.put_object(Bucket=s3_internal_bucket, Key=key, Body=content)
        undo_storage_write_unless_committed(
            session,
            StorageUndo(
                storage_type=StorageType.aws_s3_internal,
                s3_key=key,
                version_id=put["VersionId"],
            ),
        )

    def body() -> bytes:
        return s3.get_object(Bucket=s3_internal_bucket, Key=key)["Body"].read()

    with db.begin_nested():
        write(db, b"# committed\n")
    assert body() == b"# committed\n"

    nested = db.begin_nested()
    write(db, b"# rolled back\n")
    nested.rollback()
    assert body() == b"# old\n"

    # a session closed before its commit happened, like after a failed commit
    session = Session(db.connection(), join_transaction_mode="create_savepoint")
    session.begin()
    write(session, b"# never committed\n")
    session.close()
    assert body() == b"# old\n"


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


def test_sigv4_link_is_signed_for_the_public_host(monkeypatch):
    """SigV4 signs the host: with S3_PRESIGNED_URL_NETLOC set, the link is signed for that host.

    Signing for the internal host and swapping the host afterwards gives a link S3 rejects.
    """
    now = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
    monkeypatch.setattr("botocore.auth.get_current_datetime", lambda: now)
    monkeypatch.setattr(settings, "S3_PRESIGNED_URL_NETLOC", "127.0.0.1:9000")
    monkeypatch.setattr(asset_service, "_SIGV4_CLIENTS", {})
    params = {"Bucket": "bucket", "Key": "some/key.txt"}

    internal = boto3.client("s3", region_name="us-east-1", endpoint_url="http://rustfs:9000")
    signer = asset_service._sigv4_client(internal)
    link = _apply_presigned_url_netloc(
        signer.generate_presigned_url("get_object", Params=params, ExpiresIn=60)
    )

    public = boto3.client(
        "s3",
        region_name="us-east-1",
        endpoint_url="http://127.0.0.1:9000",
        config=Config(signature_version="s3v4"),
    )
    assert link == public.generate_presigned_url("get_object", Params=params, ExpiresIn=60)
