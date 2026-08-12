from uuid import UUID

from app.schemas.agent import AgentRead
from app.schemas.entity import NestedEntityRead
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead, NestedIdentifiableRead
from app.schemas.role import RoleRead
from app.schemas.utils import make_update_schema


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
