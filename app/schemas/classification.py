import uuid

from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    Schema,
)
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead


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
