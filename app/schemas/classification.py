import uuid
from typing import Annotated

from pydantic import Field

from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    Schema,
)
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead


class MTypeClassIdsCreateMixin(Schema):
    """Optional mtype class ids to attach on entity create."""

    mtype_class_ids: Annotated[
        list[uuid.UUID],
        Field(description="MType class ids to register as classifications."),
    ] = []  # ruff:ignore[mutable-class-default]


class ETypeClassIdsCreateMixin(Schema):
    """Optional etype class ids to attach on entity create."""

    etype_class_ids: Annotated[
        list[uuid.UUID],
        Field(description="EType class ids to register as classifications."),
    ] = []  # ruff:ignore[mutable-class-default]


class ClassificationBase(Schema):
    entity_id: uuid.UUID


class MTypeClassificationCreate(
    ClassificationBase, AuthorizationOptionalPublicMixin, IdentifiableCreate
):
    mtype_class_id: uuid.UUID


class MTypeClassificationRead(
    ClassificationBase,
    IdentifiableRead,
    AuthorizationMixin,
):
    mtype_class_id: uuid.UUID


class ETypeClassificationCreate(
    ClassificationBase, AuthorizationOptionalPublicMixin, IdentifiableCreate
):
    etype_class_id: uuid.UUID


class ETypeClassificationRead(
    ClassificationBase,
    IdentifiableRead,
    AuthorizationMixin,
):
    etype_class_id: uuid.UUID
