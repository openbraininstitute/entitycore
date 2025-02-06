from pydantic import BaseModel, ConfigDict

from app.schemas.agent import AgentRead
from app.schemas.base import CreationMixin
from app.schemas.entity import EntityRead
from app.schemas.role import RoleRead

# LNMC contributions
# Reconstructor full name,
# Experimenter full name,
# LNMC/BBP,
# EPFL, Switzerland


class ContributionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ContributionCreate(ContributionBase):
    agent_id: int
    role_id: int
    entity_id: int


class ContributionRead(ContributionBase, CreationMixin):
    agent: AgentRead
    role: RoleRead
    entity: EntityRead


#class ContributorRead(BaseModel):
#    agent: AgentRead
#    role: RoleRead
