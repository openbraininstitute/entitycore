
from pydantic import BaseModel

from app.schemas.agent import PersonRead
from app.schemas.base import (
    CreationMixin,
)
from app.schemas.morphology import ReconstructionMorphologyRead
from app.schemas.role import RoleRead

# LNMC contributions
# Reconstructor full name,
# Experimenter full name,
# LNMC/BBP,
# EPFL, Switzerland


class ContributionBase(BaseModel):
    class Config:
        from_attributes = True


class ContributionCreate(ContributionBase):
    agent_id: int
    role_id: int
    entity_id: int


class ContributionRead(ContributionBase, CreationMixin):
    agent: PersonRead
    role: RoleRead
    entity: ReconstructionMorphologyRead
