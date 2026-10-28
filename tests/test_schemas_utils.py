import pytest
from pydantic import ValidationError

from app.schemas.base import AuthorizationOptionalPublicMixin, Schema
from app.schemas.utils import make_update_schema


class _ExampleCreate(Schema, AuthorizationOptionalPublicMixin):
    name: str
    secret: str


def test_make_update_schema_default_exclusions():
    update = make_update_schema(_ExampleCreate, "ExampleUserUpdate")
    assert "authorized_public" not in update.model_fields
    assert sorted(update.model_fields) == ["name", "secret"]
    assert update.model_config.get("extra") == "forbid"


def test_make_update_schema_empty_exclusions_opt_out():
    update = make_update_schema(_ExampleCreate, "ExampleAdminUpdate", excluded_fields=set())
    assert "authorized_public" in update.model_fields
    update.model_validate({"authorized_public": True})


def test_make_update_schema_merges_default_exclusions():
    update = make_update_schema(_ExampleCreate, "ExampleMergedUpdate", excluded_fields={"secret"})
    assert sorted(update.model_fields) == ["name"]
    assert "authorized_public" not in update.model_fields
    assert "secret" not in update.model_fields


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "x", "authorized_public": True},
        {"name": "x", "unknown": 1},
    ],
)
def test_make_update_schema_forbids_excluded_and_unknown(payload):
    update = make_update_schema(_ExampleCreate, "ExampleForbidUpdate")
    with pytest.raises(ValidationError) as exc_info:
        update.model_validate(payload)
    assert exc_info.value.errors()[0]["type"] == "extra_forbidden"
