import pytest
import sqlalchemy as sa

from app import errors as test_module
from app.db.model import License, Subject

from tests.utils import MISSING_ID


def test_errors():
    error = test_module.ApiError(
        message="Test error",
        error_code=test_module.ApiErrorCode.INVALID_REQUEST,
    )

    assert isinstance(error, Exception)
    assert error.message == "Test error"
    assert error.error_code == "INVALID_REQUEST"
    assert error.http_status_code == 400
    assert error.details is None

    assert repr(error) == (
        "ApiError(message='Test error', error_code=INVALID_REQUEST, "
        "http_status_code=400, details=None)"
    )
    assert str(error) == (
        "message='Test error' error_code=INVALID_REQUEST http_status_code=400 details=None"
    )


def test_ensure_result(db):
    with (
        pytest.raises(test_module.ApiError) as exc_info,
        test_module.ensure_result(error_message="Custom error"),
    ):
        db.execute(sa.select(Subject)).scalar_one()

    assert exc_info.value.http_status_code == 404
    assert exc_info.value.error_code == test_module.ApiErrorCode.ENTITY_NOT_FOUND
    assert exc_info.value.message == "Custom error"


def test_ensure_uniqueness(db):
    query = sa.insert(License).values(
        id=MISSING_ID, name="Test License", description="a license description", label="test label"
    )
    db.execute(query)
    with (
        pytest.raises(test_module.ApiError) as exc_info,
        test_module.ensure_uniqueness(error_message="Custom error"),
    ):
        db.execute(query)

    assert exc_info.value.http_status_code == 409
    assert exc_info.value.error_code == test_module.ApiErrorCode.ENTITY_DUPLICATED
    assert exc_info.value.message == "Custom error"
