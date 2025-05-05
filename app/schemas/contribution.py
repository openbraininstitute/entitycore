import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import AgentRead
from app.schemas.base import CreationMixin, IdentifiableMixin
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
    agent_id: uuid.UUID
    role_id: uuid.UUID
    entity_id: uuid.UUID


class ContributionRead(ContributionBase, CreationMixin, IdentifiableMixin):
    agent: AgentRead
    role: RoleRead
    entity: EntityRead


class ContributionReadWithoutEntity(ContributionBase, CreationMixin, IdentifiableMixin):
    agent: AgentRead
    role: RoleRead


class ContributionReadWithoutEntityMixin(BaseModel):
    contributions: list[ContributionReadWithoutEntity] | None
