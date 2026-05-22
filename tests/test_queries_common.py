import uuid
from http import HTTPStatus
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from app.db.model import Derivation, TaskActivity
from app.errors import ApiError, ApiErrorCode
from app.queries.common import router_update_activity_one, router_update_one
from app.schemas.activity import ActivityUpdate
from app.schemas.derivation import DerivationRead


class _DerivationLabelPatch(BaseModel):
    label: str | None = None


def test_router_update_raises_without_authorized_project_column(db, user_context_user_1):
    with pytest.raises(ApiError) as excinfo:
        router_update_one(
            id_=uuid.uuid4(),
            db=db,
            db_model_class=Derivation,
            user_context=user_context_user_1,
            json_model=_DerivationLabelPatch(label="x"),
            response_schema_class=DerivationRead,
            check_authorized_project=True,
        )
    assert excinfo.value.error_code == ApiErrorCode.GENERIC_ERROR
    assert excinfo.value.http_status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert "authorized_project_id" in excinfo.value.message


def test_router_update_activity_raises_without_authorized_project_column(db, user_context_user_1):
    with (
        patch("app.queries.common.get_declaring_class", return_value=None),
        pytest.raises(ApiError) as excinfo,
    ):
        router_update_activity_one(
            id_=uuid.uuid4(),
            db=db,
            db_model_class=TaskActivity,
            user_context=user_context_user_1,
            json_model=ActivityUpdate(),
            response_schema_class=DerivationRead,
            check_authorized_project=True,
        )
    assert excinfo.value.error_code == ApiErrorCode.GENERIC_ERROR
    assert excinfo.value.http_status_code == HTTPStatus.INTERNAL_SERVER_ERROR
