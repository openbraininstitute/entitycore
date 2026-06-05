# app/schemas/generic_result.py

from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    NameDescriptionMixin,
)
from app.schemas.utils import make_update_schema


class GenericResultBase(BaseModel, NameDescriptionMixin):
    model_config = ConfigDict(from_attributes=True)


class GenericResultCreate(GenericResultBase, AuthorizationOptionalPublicMixin):
    data_payload: dict[str, Any] = {}
    result_type: str = "generic_result"


GenericResultUserUpdate = make_update_schema(GenericResultCreate, "GenericResultUserUpdate")  # pyright: ignore [reportInvalidTypeForm]
GenericResultAdminUpdate = make_update_schema(
    GenericResultCreate,
    "GenericResultAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedGenericResultRead(GenericResultBase, EntityTypeMixin, IdentifiableMixin):
    pass


class GenericResultRead(
    NestedGenericResultRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
):
    result_type: str
    data_payload: dict[str, Any] | None
