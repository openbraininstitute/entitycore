from __future__ import annotations

from uuid import UUID  # ruff:ignore[typing-only-standard-library-import]

# from uuid import UUID
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead, NestedIdentifiableRead
from app.schemas.role import RoleRead  # ruff:ignore[typing-only-first-party-import]
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


from app.schemas.agent import (  # ruff:ignore[module-import-not-at-top-of-file]
    AgentRead,  # ruff:ignore[typing-only-first-party-import]
)
from app.schemas.entity import (  # ruff:ignore[module-import-not-at-top-of-file]
    NestedEntityRead,  # ruff:ignore[typing-only-first-party-import]
)

NestedContributionRead.model_rebuild()
ContributionRead.model_rebuild()
