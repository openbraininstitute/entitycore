from app.schemas.base import Schema
from app.schemas.identifiable import IdentifiableCreate, NestedIdentifiableRead
from app.schemas.utils import make_update_schema


class RoleBase(Schema):
    name: str
    role_id: str


class RoleCreate(RoleBase, IdentifiableCreate):
    pass


class RoleRead(RoleBase, NestedIdentifiableRead):
    pass


RoleAdminUpdate = make_update_schema(
    RoleCreate,
    "RoleAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
