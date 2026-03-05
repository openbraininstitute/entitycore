"""Entity schemas."""

import uuid

from pydantic import UUID4, BaseModel, ConfigDict, RootModel

from app.schemas.agent import CreatedByUpdatedByMixin


class NestedEntityCreate(BaseModel):
    """Entity model to be used for bare nested entities in create endpoints."""

    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class NestedEntityRead(BaseModel):
    """Entity model to be used for bare nested entities in read endpoints."""

    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: str
    authorized_project_id: UUID4
    authorized_public: bool


class EntityRead(NestedEntityRead, CreatedByUpdatedByMixin):
    """Entity model that includes created_by and updated_by information."""


class EntityCountRead(RootModel[dict[str, int]]):
    """Entity count model that contains the number of entities by type."""
