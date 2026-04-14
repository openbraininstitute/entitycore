import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
    make_update_schema,
)


class PersonBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    given_name: str | None = None
    family_name: str | None = None
    pref_label: str


class PersonCreate(PersonBase):
    legacy_id: str | None = None


PersonAdminUpdate = make_update_schema(
    PersonCreate,
    "PersonAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedPersonRead(PersonBase, IdentifiableMixin):
    type: str
    sub_id: uuid.UUID | None


class CreatedByUpdatedByMixin(BaseModel):
    created_by: NestedPersonRead
    updated_by: NestedPersonRead


class PersonRead(NestedPersonRead, CreationMixin, CreatedByUpdatedByMixin):
    pass


class OrganizationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pref_label: str
    alternative_name: str | None = None


class OrganizationCreate(OrganizationBase):
    legacy_id: str | None = None


OrganizationAdminUpdate = make_update_schema(
    OrganizationCreate,
    "OrganizationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedOrganizationRead(OrganizationBase, IdentifiableMixin):
    type: str


class OrganizationRead(
    NestedOrganizationRead, CreationMixin, CreatedByUpdatedByMixin, IdentifiableMixin
):
    pass


class ConsortiumBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pref_label: str
    alternative_name: str | None = None


class ConsortiumCreate(ConsortiumBase):
    legacy_id: str | None = None


ConsortiumAdminUpdate = make_update_schema(
    ConsortiumCreate,
    "ConsortiumAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedConsortiumRead(ConsortiumBase, IdentifiableMixin):
    type: str


class ConsortiumRead(
    NestedConsortiumRead, CreationMixin, CreatedByUpdatedByMixin, IdentifiableMixin
):
    pass


type AgentRead = NestedPersonRead | NestedOrganizationRead | NestedConsortiumRead
