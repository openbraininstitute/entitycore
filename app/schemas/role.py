from pydantic import BaseModel, ConfigDict

from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
)
from app.schemas.utils import make_update_schema


class RoleBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    role_id: str


class RoleCreate(RoleBase):
    pass


class RoleRead(RoleBase, CreationMixin, IdentifiableMixin):
    pass


RoleAdminUpdate = make_update_schema(
    RoleCreate,
    "RoleAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
