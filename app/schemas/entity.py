import uuid

from pydantic import UUID4, BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin


class NestedEntityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: str
    authorized_project_id: UUID4
    authorized_public: bool


class EntityRead(NestedEntityRead, CreatedByUpdatedByMixin):
    pass
