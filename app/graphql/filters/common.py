import strawberry

from app.filters.common import AgentFilter, MTypeClassFilter, StrainFilter


@strawberry.experimental.pydantic.input(model=MTypeClassFilter, all_fields=True)
class MTypeClassFilterInput:
    pass


@strawberry.experimental.pydantic.input(model=StrainFilter, all_fields=True)
class StrainFilterInput:
    pass


@strawberry.experimental.pydantic.input(model=AgentFilter, all_fields=True)
class AgentFilterInput:
    pass
