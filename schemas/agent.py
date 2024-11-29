from pydantic import BaseModel

from typing import Optional

from schemas.base import (
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
    legacy_id: Optional[str] = None
    class Config:
        orm_mode = True
        from_attributes = True

class PersonCreate(PersonBase):
    pass


class PersonRead(PersonBase,CreationMixin):
    pass