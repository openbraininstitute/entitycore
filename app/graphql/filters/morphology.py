import strawberry

from app.filters.morphology import MorphologyFilter


@strawberry.experimental.pydantic.input(model=MorphologyFilter, all_fields=True)
class MorphologyFilterInput:
    pass
