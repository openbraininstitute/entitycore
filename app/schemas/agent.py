from pydantic import BaseModel, ConfigDict

from app.schemas.base import (
    CreationMixin,
)


class PersonBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    givenName: str
    familyName: str
    pref_label: str


class PersonCreate(PersonBase):
    legacy_id: str | None = None


class PersonRead(PersonBase, CreationMixin):
    type: str


class OrganizationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pref_label: str
    alternative_name: str | None = None


class OrganizationCreate(OrganizationBase):
    legacy_id: str | None = None


class OrganizationRead(OrganizationBase, CreationMixin):
    type: str


type AgentRead = PersonRead | OrganizationRead
