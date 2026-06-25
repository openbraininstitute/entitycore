import uuid

from app.db.types import AgentType
from app.schemas.base import (
    Schema,
)
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead, NestedIdentifiableRead
from app.schemas.utils import make_update_schema


class PersonBase(Schema):
    given_name: str | None = None
    family_name: str | None = None
    pref_label: str


class PersonCreate(PersonBase, IdentifiableCreate):
    legacy_id: str | None = None


PersonAdminUpdate = make_update_schema(
    PersonCreate,
    "PersonAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedPersonRead(PersonBase, NestedIdentifiableRead):
    type: AgentType
    sub_id: uuid.UUID | None


class PersonRead(PersonBase, IdentifiableRead):
    type: AgentType
    sub_id: uuid.UUID | None


class OrganizationBase(Schema):
    pref_label: str
    alternative_name: str | None = None


class OrganizationCreate(OrganizationBase, IdentifiableCreate):
    legacy_id: str | None = None


OrganizationAdminUpdate = make_update_schema(
    OrganizationCreate,
    "OrganizationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedOrganizationRead(OrganizationBase, NestedIdentifiableRead):
    type: AgentType


class OrganizationRead(
    OrganizationBase,
    IdentifiableRead,
):
    type: AgentType


class ConsortiumBase(Schema):
    pref_label: str
    alternative_name: str | None = None


class ConsortiumCreate(ConsortiumBase, IdentifiableCreate):
    legacy_id: str | None = None


ConsortiumAdminUpdate = make_update_schema(
    ConsortiumCreate,
    "ConsortiumAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedConsortiumRead(ConsortiumBase, NestedIdentifiableRead):
    type: AgentType


class ConsortiumRead(
    ConsortiumBase,
    IdentifiableRead,
):
    type: AgentType


type AgentRead = NestedPersonRead | NestedOrganizationRead | NestedConsortiumRead
