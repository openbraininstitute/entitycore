from pydantic import BaseModel
from schemas.agent import PersonRead
from schemas.morphology import ReconstructionMorphologyRead
from schemas.role import RoleRead
from typing import Union

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
    role_id: int
    entity_id: int

class ContributionRead(ContributionBase, CreationMixin):
    agent: Union[PersonRead] 
    role: RoleRead
    entity: Union[ReconstructionMorphologyRead]