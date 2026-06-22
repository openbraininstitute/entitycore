from __future__ import annotations

from uuid import UUID  # noqa: TC003

# from uuid import UUID
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead, NestedIdentifiableRead
from app.schemas.role import RoleRead  # noqa: TC001
from app.schemas.utils import make_update_schema

# LNMC contributions
# Reconstructor full name,
# Experimenter full name,
# LNMC/BBP,
# EPFL, Switzerland


class ContributionCreate(IdentifiableCreate):
    agent_id: UUID
    role_id: UUID
    entity_id: UUID


ContributionUserUpdate = make_update_schema(ContributionCreate, "ContributionUserUpdate")  # pyright: ignore [reportInvalidTypeForm]
ContributionAdminUpdate = make_update_schema(
    ContributionCreate,
    "ContributionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedContributionRead(NestedIdentifiableRead):
    agent: AgentRead
    role: RoleRead


class ContributionRead(IdentifiableRead):
    agent: AgentRead
    role: RoleRead
    entity: NestedEntityRead


class ContributionReadWithoutEntityMixin:
    contributions: list[NestedContributionRead] | None


from app.schemas.agent import AgentRead  # noqa: E402, TC001
from app.schemas.entity import NestedEntityRead  # noqa: E402, TC001

NestedContributionRead.model_rebuild()
ContributionRead.model_rebuild()
