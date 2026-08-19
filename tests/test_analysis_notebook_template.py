import pytest

from app.config import settings
from app.db.model import AnalysisNotebookTemplate, Role
from app.db.types import EntityType

from .utils import (
    MISSING_ID,
    PROJECT_ID,
    UNRELATED_PROJECT_ID,
    add_contribution,
    add_db,
    assert_request,
    check_authorization,
    check_creation_fields,
    check_entity_delete_one,
    check_entity_read_many,
    check_entity_update_one,
    check_missing,
    check_pagination,
    upload_entity_asset,
)

ROUTE = "analysis-notebook-template"
ADMIN_ROUTE = "/admin/analysis-notebook-template"
MODEL = AnalysisNotebookTemplate


@pytest.fixture
def json_data(analysis_notebook_template_json_data):
    return analysis_notebook_template_json_data


@pytest.fixture
def model(analysis_notebook_template):
    return analysis_notebook_template


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
    assert data["scale"] == json_data["scale"]
    assert data["type"] == EntityType.analysis_notebook_template
    assert data["specifications"]["python"] == json_data["specifications"]["python"]
    assert len(data["specifications"]["inputs"]) == len(json_data["specifications"]["inputs"])
    assert (
        data["specifications"]["docker"]["image_repository"]
        == json_data["specifications"]["docker"]["image_repository"]
    )
    assert data["assignment_id"] == json_data["assignment_id"]
    assert "contributions" in data

    check_creation_fields(data)


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
    data = assert_request(client_admin.get, url=f"/admin/{ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_read_many_1(client, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}").json()["data"]

    assert len(data) == 1

    assert data[0]["id"] == str(model.id)
    _assert_read_response(data[0], json_data)


def test_read_many_2(clients, json_data):
    check_entity_read_many(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
    )


def test_filter_by_assignment_id(client, json_data):
    assignment_a = "assignment-101"
    assignment_b = "physiology_basics"
    assignment_c = "no-such-assignment"

    id_a1 = assert_request(
        client.post, url=ROUTE, json=json_data | {"name": "a1", "assignment_id": assignment_a}
    ).json()["id"]
    id_a2 = assert_request(
        client.post, url=ROUTE, json=json_data | {"name": "a2", "assignment_id": assignment_a}
    ).json()["id"]
    id_b = assert_request(
        client.post, url=ROUTE, json=json_data | {"name": "b", "assignment_id": assignment_b}
    ).json()["id"]
    assert_request(client.post, url=ROUTE, json=json_data | {"name": "none", "assignment_id": None})

    data = assert_request(client.get, url=ROUTE, params={"assignment_id": assignment_a}).json()[
        "data"
    ]
    assert {d["id"] for d in data} == {id_a1, id_a2}

    data = assert_request(
        client.get, url=ROUTE, params={"assignment_id__in": [assignment_a, assignment_b]}
    ).json()["data"]
    assert {d["id"] for d in data} == {id_a1, id_a2, id_b}

    data = assert_request(
        client.get, url=ROUTE, params={"assignment_id__in": [assignment_c]}
    ).json()["data"]
    assert data == []

    data = assert_request(client.get, url=ROUTE, params={"lifecycle_status": "active"}).json()[
        "data"
    ]
    assert len(data) == 4


@pytest.mark.parametrize("assignment_id", ["", "x" * 256])
def test_assignment_id_invalid(client, json_data, assignment_id):
    assert_request(
        client.post,
        url=ROUTE,
        json=json_data | {"assignment_id": assignment_id},
        expected_status_code=422,
    )


def test_delete_one(db, clients, json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        expected_counts_before={
            AnalysisNotebookTemplate: 1,
        },
        expected_counts_after={
            AnalysisNotebookTemplate: 0,
        },
    )


def test_clone_forbidden_not_admin_of_notebook_project(client_user_2, model):
    """user_2 is not in PROJECT_ID, so cannot clone the notebook."""
    assert_request(
        client_user_2.post,
        url=f"{ROUTE}/{model.id}/clone",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
        expected_status_code=404,
    )


def test_clone_forbidden_not_admin_of_target_project(client, model):
    """user_1 is admin of PROJECT_ID but not of UNRELATED_PROJECT_ID."""
    assert_request(
        client.post,
        url=f"{ROUTE}/{model.id}/clone",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
        expected_status_code=403,
    )


def test_clone_forbidden_member_not_admin(client_user_3, model):
    """user_3 is a member of PROJECT_ID, not an admin."""
    assert_request(
        client_user_3.post,
        url=f"{ROUTE}/{model.id}/clone",
        json={"target_project_ids": [PROJECT_ID]},
        expected_status_code=403,
    )


def test_clone_missing_notebook(client):
    assert_request(
        client.post,
        url=f"{ROUTE}/{MISSING_ID}/clone",
        json={"target_project_ids": [PROJECT_ID]},
        expected_status_code=404,
    )


def test_clone_forbidden_source_in_target(client, model):
    """Source project cannot be listed as a target project."""
    assert_request(
        client.post,
        url=f"{ROUTE}/{model.id}/clone",
        json={"target_project_ids": [PROJECT_ID]},
        expected_status_code=403,
    )


def test_clone_forbidden_public_source(client, json_data):
    """Source notebook must be private; cloning a public one returns 403."""
    notebook_id = assert_request(
        client.post, url=ROUTE, json=json_data | {"authorized_public": True}
    ).json()["id"]
    assert_request(
        client.post,
        url=f"{ROUTE}/{notebook_id}/clone",
        json={"target_project_ids": [PROJECT_ID]},
        expected_status_code=403,
    )


def test_clone_forbidden_public_existing_in_target(
    client_user_1_two_projects, db, json_data, user_id
):
    """If a public notebook with the same name already exists in the target project, return 403."""
    notebook_id = assert_request(
        client_user_1_two_projects.post, url=ROUTE, json=json_data | {"authorized_public": False}
    ).json()["id"]
    add_db(
        db,
        AnalysisNotebookTemplate(
            **json_data
            | {
                "created_by_id": user_id,
                "updated_by_id": user_id,
                "authorized_project_id": UNRELATED_PROJECT_ID,
                "authorized_public": True,
            },
        ),
    )
    assert_request(
        client_user_1_two_projects.post,
        url=f"{ROUTE}/{notebook_id}/clone",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
        expected_status_code=403,
    )


def test_clone_creates_private_copies_in_target_projects(client_user_1_two_projects, model):
    """Cloned notebooks are always private, one per target project."""
    data = assert_request(
        client_user_1_two_projects.post,
        url=f"{ROUTE}/{model.id}/clone",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
    ).json()
    assert len(data["created"]) == 1
    clone = data["created"][0]
    assert clone["authorized_public"] is False
    assert clone["authorized_project_id"] == UNRELATED_PROJECT_ID
    assert clone["name"] == model.name
    assert clone["assets"] == []
    assert clone["contributions"] == []


def test_clone_member_can_read_cloned_notebook(client_user_1_two_projects, client_user_2, model):
    """User with admin on both projects clones into UNRELATED_PROJECT_ID.
    user_2 (member) can read it.
    """
    asset_response = upload_entity_asset(
        client_user_1_two_projects,
        EntityType.analysis_notebook_template,
        model.id,
        files={"file": ("notebook.ipynb", b"{}", "application/x-ipynb+json")},
        label="jupyter_notebook",
    ).json()

    data = assert_request(
        client_user_1_two_projects.post,
        url=f"{ROUTE}/{model.id}/clone",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
    ).json()

    assert len(data["created"]) == 1
    clone_id = data["created"][0]["id"]

    assert len(data["created"][0]["assets"]) == 1

    assert_request(client_user_2.get, url=f"{ROUTE}/{clone_id}")
    clone_asset_id = data["created"][0]["assets"][0]["id"]
    assert clone_asset_id != asset_response["id"]

    assert_request(
        client_user_2.get,
        url=f"{ROUTE}/{clone_id}/assets/{clone_asset_id}/download",
        expected_status_code=307,
        follow_redirects=False,
    )


def test_clone_upserts_existing_notebook_with_assets(client_user_1_two_projects, model):
    """Cloning twice: first call creates, second call updates and replaces assets."""
    first = assert_request(
        client_user_1_two_projects.post,
        url=f"{ROUTE}/{model.id}/clone",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
    ).json()["created"][0]
    existing_id = first["id"]
    assert first["assets"] == []

    upload_entity_asset(
        client_user_1_two_projects,
        EntityType.analysis_notebook_template,
        model.id,
        files={"file": ("new.ipynb", b"{}", "application/x-ipynb+json")},
        label="jupyter_notebook",
    )

    second = assert_request(
        client_user_1_two_projects.post,
        url=f"{ROUTE}/{model.id}/clone",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
    ).json()["created"][0]

    assert second["id"] == existing_id
    assert len(second["assets"]) == 1
    assert second["assets"][0]["path"] == "new.ipynb"


def test_clone_upserts_reflects_source_changes(client_user_1_two_projects, model):
    """Clone, then mutate source (swap asset + update field), clone again: target mirrors source."""
    old_asset_id = upload_entity_asset(
        client_user_1_two_projects,
        EntityType.analysis_notebook_template,
        model.id,
        files={"file": ("old.ipynb", b"{}", "application/x-ipynb+json")},
        label="jupyter_notebook",
    ).json()["id"]

    first = assert_request(
        client_user_1_two_projects.post,
        url=f"{ROUTE}/{model.id}/clone",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
    ).json()["created"][0]
    existing_id = first["id"]
    assert len(first["assets"]) == 1

    assert_request(
        client_user_1_two_projects.delete,
        url=f"{ROUTE}/{model.id}/assets/{old_asset_id}",
    )
    assert_request(
        client_user_1_two_projects.patch,
        url=f"{ROUTE}/{model.id}",
        json={"description": "updated description"},
    )
    upload_entity_asset(
        client_user_1_two_projects,
        EntityType.analysis_notebook_template,
        model.id,
        files={"file": ("new.ipynb", b"{}", "application/x-ipynb+json")},
        label="jupyter_notebook",
    )

    second = assert_request(
        client_user_1_two_projects.post,
        url=f"{ROUTE}/{model.id}/clone",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
    ).json()["created"][0]

    assert second["id"] == existing_id
    assert second["description"] == "updated description"
    assert len(second["assets"]) == 1
    assert second["assets"][0]["path"] == "new.ipynb"


def test_clone_syncs_contributions(
    client_user_1_two_projects, db, json_data, user_id, person_id, role_id
):
    """Clone replaces target contributions to match source: removes old, adds new."""
    notebook_id = assert_request(
        client_user_1_two_projects.post, url=ROUTE, json=json_data | {"authorized_public": False}
    ).json()["id"]
    add_contribution(db, notebook_id, person_id, role_id, user_id)

    target = add_db(
        db,
        AnalysisNotebookTemplate(
            **json_data
            | {
                "created_by_id": user_id,
                "updated_by_id": user_id,
                "authorized_project_id": UNRELATED_PROJECT_ID,
                "authorized_public": False,
            },
        ),
    )
    other_role = add_db(
        db,
        Role(role_id="other-role", name="other-role", created_by_id=user_id, updated_by_id=user_id),
    )
    add_contribution(db, target.id, person_id, other_role.id, user_id)

    data = assert_request(
        client_user_1_two_projects.post,
        url=f"{ROUTE}/{notebook_id}/clone",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
    ).json()

    contribs = data["created"][0]["contributions"]
    assert len(contribs) == 1
    assert contribs[0]["role"]["id"] == str(role_id)


def test_clone_syncs_contributions_already_matching(
    client_user_1_two_projects, db, json_data, user_id, person_id, role_id
):
    """If target already has the same contrib as source, it is kept and no duplicate is created."""
    notebook_id = assert_request(
        client_user_1_two_projects.post, url=ROUTE, json=json_data | {"authorized_public": False}
    ).json()["id"]
    add_contribution(db, notebook_id, person_id, role_id, user_id)

    target = add_db(
        db,
        AnalysisNotebookTemplate(
            **json_data
            | {
                "created_by_id": user_id,
                "updated_by_id": user_id,
                "authorized_project_id": UNRELATED_PROJECT_ID,
                "authorized_public": False,
            },
        ),
    )
    add_contribution(db, target.id, person_id, role_id, user_id)

    data = assert_request(
        client_user_1_two_projects.post,
        url=f"{ROUTE}/{notebook_id}/clone",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
    ).json()

    contribs = data["created"][0]["contributions"]
    assert len(contribs) == 1
    assert contribs[0]["role"]["id"] == str(role_id)


def test_clone_auth_disabled(monkeypatch, client, model):
    """When APP_DISABLE_AUTH is True, admin check on target project is bypassed."""
    monkeypatch.setattr(settings, "APP_DISABLE_AUTH", True)
    data = assert_request(
        client.post,
        url=f"{ROUTE}/{model.id}/clone",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
    ).json()
    assert len(data["created"]) == 1
    assert data["created"][0]["authorized_project_id"] == UNRELATED_PROJECT_ID


def test_delete_clones_forbidden_not_admin_of_notebook_project(client_user_2, model):
    """user_2 is not in PROJECT_ID, so cannot delete clones."""
    assert_request(
        client_user_2.post,
        url=f"{ROUTE}/{model.id}/delete-clones",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
        expected_status_code=404,
    )


def test_delete_clones_forbidden_not_admin_of_target_project(client, model):
    """user_1 is admin of PROJECT_ID but not of UNRELATED_PROJECT_ID."""
    assert_request(
        client.post,
        url=f"{ROUTE}/{model.id}/delete-clones",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
        expected_status_code=403,
    )


def test_delete_clones_forbidden_member_not_admin(client_user_3, model):
    """user_3 is a member of PROJECT_ID, not an admin."""
    assert_request(
        client_user_3.post,
        url=f"{ROUTE}/{model.id}/delete-clones",
        json={"target_project_ids": [PROJECT_ID]},
        expected_status_code=403,
    )


def test_delete_clones_forbidden_source_in_target(client, model):
    """Source project cannot be listed as a target project."""
    assert_request(
        client.post,
        url=f"{ROUTE}/{model.id}/delete-clones",
        json={"target_project_ids": [PROJECT_ID]},
        expected_status_code=403,
    )


def test_delete_clones_forbidden_public_source(client, json_data):
    """Source notebook must be private."""
    notebook_id = assert_request(
        client.post, url=ROUTE, json=json_data | {"authorized_public": True}
    ).json()["id"]
    assert_request(
        client.post,
        url=f"{ROUTE}/{notebook_id}/delete-clones",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
        expected_status_code=403,
    )


def test_delete_clones_success(client_user_1_two_projects, model):
    """Clone into target, then delete-clones: target notebook is gone."""
    clone_data = assert_request(
        client_user_1_two_projects.post,
        url=f"{ROUTE}/{model.id}/clone",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
    ).json()
    clone_id = clone_data["created"][0]["id"]

    data = assert_request(
        client_user_1_two_projects.post,
        url=f"{ROUTE}/{model.id}/delete-clones",
        json={"target_project_ids": [UNRELATED_PROJECT_ID]},
    ).json()

    assert len(data["deleted"]) == 1
    assert data["deleted"][0]["id"] == clone_id

    assert_request(
        client_user_1_two_projects.get,
        url=f"{ROUTE}/{clone_id}",
        expected_status_code=404,
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, json_data):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)
