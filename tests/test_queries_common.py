import uuid
from http import HTTPStatus
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from app.db.model import Derivation, TaskActivity
from app.errors import ApiError, ApiErrorCode
from app.filters.cell_morphology import CellMorphologyFilter
from app.queries.common import (
    _sort_is_creation_date_first,
    router_update_activity_one,
    router_update_one,
)
from app.schemas.activity import ActivityUpdate
from app.schemas.derivation import DerivationRead


class _DerivationLabelPatch(BaseModel):
    label: str | None = None


@pytest.mark.parametrize(
    ("order_by", "expected"),
    [
        (None, True),  # no ordering_values → default behaviour
        (["-creation_date"], True),  # explicit descending creation_date
        (["creation_date"], False),  # ascending creation_date is a different sort
        (["+creation_date"], False),  # explicitly ascending creation_date
        (["name"], False),  # non-creation_date primary sort
        (["-name"], False),  # non-creation_date primary sort (descending)
        (["-creation_date", "name"], True),  # creation_date DESC is still the primary sort
        (["name", "-creation_date"], False),  # name is the primary sort
    ],
)
def test_sort_is_creation_date_first(order_by, expected):
    filter_model = (
        CellMorphologyFilter(order_by=order_by) if order_by is not None else CellMorphologyFilter()
    )
    assert _sort_is_creation_date_first(filter_model) is expected


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
        patch("app.queries.common.get_authorized_project_id_declaring_class", return_value=None),
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
