from uuid import UUID

import pytest

from app.config import settings
from app.errors import ApiError, ApiErrorCode
from app.schemas.auth import UserContext, UserProfile, UserProjectGroup
from app.utils import virtual_lab as test_module

from tests.utils import PROJECT_ID, UNRELATED_PROJECT_ID, USER_SUB_ID_1, VIRTUAL_LAB_ID


def _user_context(*, virtual_lab_id=None, project_id=None, groups=None):
    return UserContext(
        profile=UserProfile(subject=UUID(USER_SUB_ID_1), name="User"),
        expiration=None,
        is_authorized=True,
        virtual_lab_id=virtual_lab_id,
        project_id=project_id,
        user_project_groups=groups or [],
    )


def test_resolve_virtual_lab_id_from_groups():
    user_context = _user_context(
        virtual_lab_id=UUID(VIRTUAL_LAB_ID),
        project_id=UUID(PROJECT_ID),
        groups=[
            UserProjectGroup(
                virtual_lab_id=UUID(VIRTUAL_LAB_ID),
                project_id=UUID(PROJECT_ID),
                role="admin",
            )
        ],
    )
    assert test_module.resolve_virtual_lab_id(user_context, UUID(PROJECT_ID)) == UUID(VIRTUAL_LAB_ID)


def test_resolve_virtual_lab_id_not_found_raises():
    user_context = _user_context(project_id=UUID(PROJECT_ID), groups=[])
    with pytest.raises(ApiError) as exc_info:
        test_module.resolve_virtual_lab_id(user_context, UUID(UNRELATED_PROJECT_ID))
    assert exc_info.value.error_code == ApiErrorCode.ASSET_VIRTUAL_LAB_ID_NOT_FOUND
    assert exc_info.value.http_status_code == 422


def test_resolve_virtual_lab_id_auth_disabled_uses_header_vlab(monkeypatch):
    monkeypatch.setattr(settings, "APP_DISABLE_AUTH", True)
    # No groups, but the virtual-lab-id header is set: it takes precedence.
    user_context = _user_context(virtual_lab_id=UUID(VIRTUAL_LAB_ID), project_id=UUID(PROJECT_ID))
    assert test_module.resolve_virtual_lab_id(user_context, UUID(PROJECT_ID)) == UUID(VIRTUAL_LAB_ID)


def test_resolve_virtual_lab_id_auth_disabled_uses_fallback(monkeypatch):
    monkeypatch.setattr(settings, "APP_DISABLE_AUTH", True)
    # No groups and no virtual-lab-id header: the hardcoded fallback is used.
    user_context = _user_context(project_id=UUID(PROJECT_ID))
    assert (
        test_module.resolve_virtual_lab_id(user_context, UUID(PROJECT_ID))
        == settings.APP_DISABLE_AUTH_VIRTUAL_LAB_ID
    )
