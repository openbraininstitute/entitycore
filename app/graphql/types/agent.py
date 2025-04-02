import strawberry

from app.schemas.agent import OrganizationRead, PersonRead


@strawberry.experimental.pydantic.type(model=PersonRead, all_fields=True)
class PersonReadType:
    pass


@strawberry.experimental.pydantic.type(model=OrganizationRead, all_fields=True)
class OrganizationReadType:
    pass


AgentReadType = PersonReadType | OrganizationReadType
