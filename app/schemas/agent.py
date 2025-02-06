from pydantic import BaseModel, ConfigDict

from app.schemas.base import (
    CreationMixin,
)

# LNMC contributions
# Reconstructor full name,
# Experimenter full name,
# LNMC/BBP,
# EPFL, Switzerland


class PersonBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    givenName: str
    familyName: str
    pref_label: str


class PersonCreate(PersonBase):
    legacy_id: str | None = None


class PersonRead(PersonBase, CreationMixin):
    pass


class OrganizationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    pref_label: str
    alternative_name: str | None = None


class OrganizationCreate(OrganizationBase):
    legacy_id: str | None = None


class OrganizationRead(OrganizationBase, CreationMixin):
    pass


type AgentRead = PersonRead | OrganizationRead
