from uuid import UUID

import pytest

from app.db.model import TaskResult
from app.db.types import (
    ALLOWED_ASSET_LABELS_PER_TASK_RESULT,
    CONTENT_TYPE_TO_SUFFIX,
    AssetLabel,
    EntityType,
    LabelRequirements,
    TaskResultType,
)
from app.db.utils import allowed_asset_labels_for

from .utils import (
    PROJECT_ID,
    USER_SUB_ID_1,
    add_all_db,
    assert_request,
    check_authorization,
    check_entity_delete_one,
    check_entity_read_many,
    check_entity_read_response,
    check_entity_update_one,
    check_missing,
    check_pagination,
    upload_entity_asset,
)

ROUTE = "task-result"
ADMIN_ROUTE = "/admin/task-result"


@pytest.fixture
def json_data(task_result_json_data):
    return task_result_json_data | {"task_result_type": TaskResultType.circuit_extraction__circuit}


@pytest.fixture
def public_json_data(public_task_result_json_data):
    return public_task_result_json_data | {
        "task_result_type": TaskResultType.circuit_extraction__circuit
    }


@pytest.fixture
def model(task_result):
    return task_result


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


def _assert_read_response(data, json_data):
    check_entity_read_response(data, json_data, EntityType.task_result)


def test_user_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)
    assert not data["authorized_public"]
    assert data["authorized_project_id"] == PROJECT_ID


def test_user_read_one(client, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_admin_read_one(client_admin, model, json_data):
    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_read_many_1(clients, json_data):
    check_entity_read_many(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
    )


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
        optional_payload={},
    )


def test_user_delete_one(clients, db, json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        expected_counts_before={
            TaskResult: 1,
        },
        expected_counts_after={
            TaskResult: 0,
        },
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, public_json_data):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, public_json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


@pytest.fixture
def models(db, json_data, person_id):
    objs = [
        TaskResult(
            **json_data
            | {
                "name": f"s-{i}",
                "task_result_type": TaskResultType.circuit_extraction__circuit,
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_project_id": PROJECT_ID,
            }
        )
        for i in range(3)
    ]
    return add_all_db(db, objs)


def test_filtering(client, models):
    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    assert models is not None

    data = req({"task_result_type": TaskResultType.circuit_extraction__circuit})
    assert len(data) == len(models)

    data = req({"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1})
    assert len(data) == 3

    data = req({"name__ilike": "s-%"})
    assert len(data) == 3

    data = req({"name": "s-0"})
    assert len(data) == 1
    assert data[0]["name"] == "s-0"

    data = req({"name": "s-none"})
    assert len(data) == 0


def _example_file_upload(
    allowed: dict[AssetLabel, list[LabelRequirements]],
) -> tuple[AssetLabel, str, bytes, str]:
    for label, requirements in allowed.items():
        for requirement in requirements:
            if requirement.is_directory:
                continue
            suffix = CONTENT_TYPE_TO_SUFFIX[requirement.content_type][0]
            filename = f"file{suffix}"
            return label, filename, b"content", requirement.content_type.value
    msg = "No file-based upload example found in allowed asset labels"
    raise ValueError(msg)


def _pick_invalid_label(allowed: dict[AssetLabel, list[LabelRequirements]]) -> AssetLabel:
    for candidate in AssetLabel:
        if candidate not in allowed and candidate != AssetLabel.directory_child:
            return candidate
    msg = "Expected at least one asset label to be disallowed"
    raise ValueError(msg)


@pytest.mark.parametrize("task_result_type", TaskResultType)
def test_allowed_asset_upload_per_task_result_type(
    client, db, task_result_json_data, task_result_type
):
    allowed = ALLOWED_ASSET_LABELS_PER_TASK_RESULT[task_result_type]

    data = assert_request(
        client.post,
        url=ROUTE,
        json=task_result_json_data | {"task_result_type": task_result_type},
    ).json()
    entity_id = UUID(data["id"])

    entity = db.get(TaskResult, entity_id)
    assert allowed_asset_labels_for(entity) == allowed

    if allowed is None:
        response = upload_entity_asset(
            client,
            EntityType.task_result,
            entity_id,
            files={"file": ("morph.asc", b"content", "application/asc")},
            label=AssetLabel.morphology.value,
            expected_status=None,
        )
        assert response.status_code == 422
        assert response.json() == {
            "error_code": "ASSET_INVALID_SCHEMA",
            "message": "Asset schema is invalid",
            "details": [
                (
                    "Value error, There are no allowed asset labels defined for "
                    f"'{EntityType.task_result}'"
                )
            ],
        }
        return

    label, filename, content, content_type = _example_file_upload(allowed)
    upload_entity_asset(
        client,
        EntityType.task_result,
        entity_id,
        files={"file": (filename, content, content_type)},
        label=label.value,
    )

    invalid_label = _pick_invalid_label(allowed)
    response = upload_entity_asset(
        client,
        EntityType.task_result,
        entity_id,
        files={"file": ("morph.asc", b"content", "application/asc")},
        label=invalid_label.value,
        expected_status=None,
    )
    assert response.status_code == 422
    assert response.json()["error_code"] == "ASSET_INVALID_SCHEMA"
    assert any("is not allowed for entity type" in detail for detail in response.json()["details"])
