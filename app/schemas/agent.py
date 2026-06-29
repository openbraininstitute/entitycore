import re
import uuid
from typing import Annotated

from pydantic import AfterValidator

from app.db.types import AgentType
from app.schemas.base import (
    Schema,
)
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead, NestedIdentifiableRead
from app.schemas.utils import make_update_schema

ORCID_REGEX = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{4}$")


def validate_orcid(value: str) -> str:
    if value is None:
        return value

    value = value.strip()

    # normalize URI form
    if value.startswith("https://orcid.org/"):
        value = value.rsplit("/", 1)[-1]

    if not ORCID_REGEX.match(value):
        msg = f"Invalid ORCID: {value}"
        raise ValueError(msg)

    return value


ORCID = Annotated[str, AfterValidator(validate_orcid)]

ROR_REGEX = re.compile(r"^0[a-z0-9]{8}$")


def validate_ror(value: str) -> str:
    if value is None:
        return value

    value = value.strip().lower()

    # normalize URL form
    if value.startswith("https://ror.org/"):
        value = value.rsplit("/", 1)[-1]

    if not ROR_REGEX.match(value):
        msg = f"Invalid ROR ID: {value}"
        raise ValueError(msg)

    return value


ROR = Annotated[str, AfterValidator(validate_ror)]


class PersonBase(Schema):
    given_name: str | None = None
    family_name: str | None = None
    pref_label: str


class PersonCreate(PersonBase, IdentifiableCreate):
    legacy_id: str | None = None
    orcid: ORCID | None = None


PersonAdminUpdate = make_update_schema(
    PersonCreate,
    "PersonAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedPersonRead(PersonBase, NestedIdentifiableRead):
    type: AgentType
    sub_id: uuid.UUID | None
    orcid: ORCID | None


class PersonRead(PersonBase, IdentifiableRead):
    type: AgentType
    sub_id: uuid.UUID | None
    orcid: ORCID | None


class OrganizationBase(Schema):
    pref_label: str
    alternative_name: str


class OrganizationCreate(OrganizationBase, IdentifiableCreate):
    legacy_id: str | None = None
    ror_id: ROR | None = None


OrganizationAdminUpdate = make_update_schema(
    OrganizationCreate,
    "OrganizationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedOrganizationRead(OrganizationBase, NestedIdentifiableRead):
    type: AgentType
    ror_id: ROR | None


class OrganizationRead(
    OrganizationBase,
    IdentifiableRead,
):
    type: AgentType
    ror_id: ROR | None


class ConsortiumBase(Schema):
    pref_label: str
    alternative_name: str


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
