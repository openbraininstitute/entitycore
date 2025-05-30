from pydantic import BaseModel, ConfigDict

from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
)


class RoleBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    role_id: str


class RoleCreate(RoleBase):
    pass


class RoleRead(RoleBase, CreationMixin, IdentifiableMixin):
    pass
