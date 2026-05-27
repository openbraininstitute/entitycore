from uuid import UUID

import pytest

from app.db.model import Circuit
from app.errors import ApiError, ApiErrorCode
from app.queries.entity import get_writable_entity, get_writable_entity_by_context
from app.schemas.auth import UserContext, UserProfile

from tests.utils import PROJECT_ID, UNRELATED_PROJECT_ID, USER_SUB_ID_1, VIRTUAL_LAB_ID


def test_get_writable_entity_for_update(db, circuit):
    entity = get_writable_entity(
        db,
        Circuit,
        circuit.id,
        UUID(PROJECT_ID),
        for_update=True,
    )
    assert entity.id == circuit.id


def test_get_writable_entity_by_context(db, circuit, user_context_user_1):
    entity = get_writable_entity_by_context(
        db,
        Circuit,
        circuit.id,
        user_context_user_1,
    )
    assert entity.id == circuit.id


def test_get_writable_entity_by_context_for_update(db, circuit, user_context_user_1):
    entity = get_writable_entity_by_context(
        db,
        Circuit,
        circuit.id,
        user_context_user_1,
        for_update=True,
    )
    assert entity.id == circuit.id


def test_get_writable_entity_by_context_public_entity(db, public_circuit, user_context_user_1):
    entity = get_writable_entity_by_context(
        db,
        Circuit,
        public_circuit.id,
        user_context_user_1,
    )
    assert entity.id == public_circuit.id


def test_get_writable_entity_by_context_not_authorized(db, circuit, user_context_no_project):
    with pytest.raises(ApiError) as exc_info:
        get_writable_entity_by_context(
            db,
            Circuit,
            circuit.id,
            user_context_no_project,
        )
    assert exc_info.value.error_code == ApiErrorCode.NOT_AUTHORIZED
    assert exc_info.value.http_status_code == 403


def test_get_writable_entity_by_context_wrong_project(db, circuit, user_context_user_2):
    with pytest.raises(ApiError) as exc_info:
        get_writable_entity_by_context(
            db,
            Circuit,
            circuit.id,
            user_context_user_2,
        )
    assert exc_info.value.error_code == ApiErrorCode.ENTITY_NOT_FOUND


def test_find_virtual_lab_from_project_id(user_context_user_1):
    assert user_context_user_1.find_virtual_lab_from_project_id(UUID(PROJECT_ID)) == UUID(
        VIRTUAL_LAB_ID
    )
    assert user_context_user_1.find_virtual_lab_from_project_id(UUID(UNRELATED_PROJECT_ID)) is None


def test_find_virtual_lab_from_project_id_without_groups():
    user_context = UserContext(
        profile=UserProfile(subject=UUID(USER_SUB_ID_1), name="User"),
        expiration=None,
        is_authorized=True,
        project_id=UUID(PROJECT_ID),
        user_project_groups=[],
    )
    assert user_context.find_virtual_lab_from_project_id(UUID(PROJECT_ID)) is None
