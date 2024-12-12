from pydantic import BaseModel

from typing import Optional

from app.schemas.base import (
    CreationMixin,
)

# LNMC contributions
# Reconstructor full name,
# Experimenter full name,
# LNMC/BBP,
# EPFL, Switzerland


class PersonBase(BaseModel):
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class PersonCreate(PersonBase):
    legacy_id: Optional[str] = None
    pass


class PersonRead(PersonBase, CreationMixin):
    pass


class OrganizationBase(BaseModel):
    name: str
    label: str
    alternative_name: Optional[str] = None

    class Config:
        from_attributes = True


class OrganizationCreate(OrganizationBase):
    legacy_id: Optional[str] = None
    pass


class OrganizationRead(OrganizationBase, CreationMixin):
    pass
