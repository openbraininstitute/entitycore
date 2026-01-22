import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.base import EntityTypeMixin, IdentifiableMixin
from app.schemas.scientific_artifact import ScientificArtifactCreate, ScientificArtifactRead
from app.schemas.utils import make_update_schema


class ParameterisationRelationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    data: dict[str, Any]


class ParameterisationRelationCreate(
    ParameterisationRelationBase,
    ScientificArtifactCreate,
):
    pass


ParameterisationRelationUserUpdate = make_update_schema(
    ParameterisationRelationCreate,
    "ParameterisationRelationUserUpdate",
)  # pyright: ignore [reportInvalidTypeForm]
ParameterisationRelationAdminUpdate = make_update_schema(
    ParameterisationRelationCreate,
    "ParameterisationRelationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedParameterisationRelationRead(
    ParameterisationRelationBase,
    IdentifiableMixin,
    EntityTypeMixin,
):
    pass


class ParameterisationRelationRead(
    ParameterisationRelationBase,
    ScientificArtifactRead,
):
    pass
