from pydantic import BaseModel, ConfigDict

from app.schemas.base import (
    CreationMixin,
)


class AgentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: str


class PersonBase(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    givenName: str
    familyName: str
    pref_label: str


class PersonCreate(PersonBase):
    legacy_id: str | None = None


class PersonRead(PersonBase, CreationMixin):
    pass


class OrganizationBase(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    pref_label: str
    alternative_name: str | None = None


class OrganizationCreate(OrganizationBase):
    legacy_id: str | None = None


class OrganizationRead(OrganizationBase, CreationMixin):
    pass


type AgentRead = PersonRead | OrganizationRead
