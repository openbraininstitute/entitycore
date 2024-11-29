from pydantic import BaseModel
from schemas.agent import PersonRead

from schemas.base import (
    CreationMixin,
)

# LNMC contributions
# Reconstructor full name, 
# Experimenter full name,
# LNMC/BBP,
# EPFL, Switzerland


class ContributionBase(BaseModel):
    class Config:
        orm_mode = True
        from_attributes = True

class ContributionCreate(ContributionBase):
    agent_id: int

class ContributionRead(ContributionBase, CreationMixin):
    agent: PersonRead