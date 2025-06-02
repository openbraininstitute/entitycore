import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import AgentRead, CreatedByUpdatedByMixin
from app.schemas.base import CreationMixin, IdentifiableMixin
from app.schemas.entity import NestedEntityRead
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


class NestedContributionRead(ContributionBase, IdentifiableMixin):
    agent: AgentRead
    role: RoleRead


class ContributionRead(
    NestedContributionRead, CreationMixin, CreatedByUpdatedByMixin, IdentifiableMixin
):
    entity: NestedEntityRead


class ContributionReadWithoutEntityMixin(BaseModel):
    contributions: list[NestedContributionRead] | None
