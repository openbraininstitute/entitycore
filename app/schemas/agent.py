from pydantic import BaseModel

from app.schemas.base import (
    CreationMixin,
)

# LNMC contributions
# Reconstructor full name,
# Experimenter full name,
# LNMC/BBP,
# EPFL, Switzerland


class PersonBase(BaseModel):
    givenName: str
    familyName: str

    class Config:
        from_attributes = True


class PersonCreate(PersonBase):
    legacy_id: str | None = None


class PersonRead(PersonBase, CreationMixin):
    pass


class OrganizationBase(BaseModel):
    name: str
    label: str
    alternative_name: str | None = None

    class Config:
        from_attributes = True


class OrganizationCreate(OrganizationBase):
    legacy_id: str | None = None


class OrganizationRead(OrganizationBase, CreationMixin):
    pass
