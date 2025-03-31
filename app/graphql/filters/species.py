import strawberry

from app.filters.common import SpeciesFilter


@strawberry.experimental.pydantic.input(model=SpeciesFilter, all_fields=True)
class SpeciesFilterInput:
    pass
