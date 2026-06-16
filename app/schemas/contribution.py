from __future__ import annotations

from pydantic import UUID4, BaseModel

from app.schemas.base import Schema
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead, NestedIdentifiableRead
from app.schemas.role import RoleRead  # noqa: TC001
from app.schemas.utils import make_update_schema

# LNMC contributions
# Reconstructor full name,
# Experimenter full name,
# LNMC/BBP,
# EPFL, Switzerland


class ContributionBase(Schema):
    pass


class ContributionCreate(ContributionBase, IdentifiableCreate):
    agent_id: UUID4
    role_id: UUID4
    entity_id: UUID4


ContributionUserUpdate = make_update_schema(ContributionCreate, "ContributionUserUpdate")  # pyright: ignore [reportInvalidTypeForm]
ContributionAdminUpdate = make_update_schema(
    ContributionCreate,
    "ContributionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedContributionRead(ContributionBase, NestedIdentifiableRead):
    agent: AgentRead
    role: RoleRead


class ContributionRead(
    ContributionBase,
    IdentifiableRead,
):
    agent: AgentRead
    role: RoleRead
    entity: NestedEntityRead


class ContributionReadWithoutEntityMixin(BaseModel):
    contributions: list[NestedContributionRead] | None


from app.schemas.agent import AgentRead  # noqa: E402, TC001
from app.schemas.entity import NestedEntityRead  # noqa: E402, TC001

NestedContributionRead.model_rebuild()
ContributionRead.model_rebuild()
