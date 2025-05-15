import uuid

from pydantic import BaseModel

from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
)


class ValidationResultBase(BaseModel):
    name: str
    passed: bool
    validated_entity_id: uuid.UUID


class ValidationResultRead(ValidationResultBase, CreationMixin, IdentifiableMixin):
    pass


class ValidationResultCreate(ValidationResultBase):
    pass
