import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
)


class ClassificationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_id: uuid.UUID


class MTypeClassificationCreate(ClassificationBase, AuthorizationOptionalPublicMixin):
    mtype_class_id: uuid.UUID


class MTypeClassificationRead(
    ClassificationBase, CreatedByUpdatedByMixin, CreationMixin, AuthorizationMixin
):
    mtype_class_id: uuid.UUID


class ETypeClassificationCreate(ClassificationBase, AuthorizationOptionalPublicMixin):
    etype_class_id: uuid.UUID


class ETypeClassificationRead(
    ClassificationBase, CreatedByUpdatedByMixin, CreationMixin, AuthorizationMixin
):
    etype_class_id: uuid.UUID
