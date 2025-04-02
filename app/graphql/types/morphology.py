import strawberry

from app.schemas.morphology import ReconstructionMorphologyCreate, ReconstructionMorphologyRead


@strawberry.experimental.pydantic.type(model=ReconstructionMorphologyRead, all_fields=True)
class MorphologyType:
    pass


@strawberry.experimental.pydantic.input(model=ReconstructionMorphologyCreate, all_fields=True)
class MorphologyInput:
    pass
