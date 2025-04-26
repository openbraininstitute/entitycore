from pydantic import BaseModel, ConfigDict
from app.schemas.base import CreationMixin, IdentifiableMixin

from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
)

class PersonBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    givenName: str
    familyName: str
    pref_label: str

class PersonRead(PersonBase, CreationMixin, IdentifiableMixin):
    type: str

class PersonCreate(PersonBase):
    legacy_id: str | None = None

class OrganizationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pref_label: str
    alternative_name: str | None = None

class OrganizationCreate(OrganizationBase):
    legacy_id: str | None = None


class OrganizationRead(OrganizationBase, CreationMixin, IdentifiableMixin):
    type: str


type AgentRead = PersonRead | OrganizationRead
