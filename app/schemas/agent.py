import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
)


class PersonBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    given_name: str | None = None
    family_name: str | None = None
    pref_label: str


class PersonCreate(PersonBase):
    legacy_id: str | None = None


class PersonRead(PersonBase, CreationMixin, IdentifiableMixin):
    type: str
    sub_id: uuid.UUID | None


class OrganizationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pref_label: str
    alternative_name: str | None = None


class OrganizationCreate(OrganizationBase):
    legacy_id: str | None = None


class OrganizationRead(OrganizationBase, CreationMixin, IdentifiableMixin):
    type: str


type AgentRead = PersonRead | OrganizationRead


class CreatedByUpdatedByMixin(BaseModel):
    created_by: PersonRead
    updated_by: PersonRead
