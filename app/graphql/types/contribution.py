import strawberry

from app.graphql.types.agent import AgentReadType
from app.schemas.contribution import ContributionReadWithoutEntity


@strawberry.experimental.pydantic.type(model=ContributionReadWithoutEntity)
class ContributionReadWithoutEntityType:
    id: strawberry.auto
    agent: AgentReadType
    role: strawberry.auto
    creation_date: strawberry.auto
    update_date: strawberry.auto
