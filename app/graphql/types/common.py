import strawberry

from app.schemas.base import (
    BrainRegionRead,
    LicenseRead,
    PointLocationBase,
    SpeciesCreate,
    SpeciesRead,
    StrainRead,
)


@strawberry.experimental.pydantic.type(model=LicenseRead, all_fields=True)
class LicenseReadType:
    pass


@strawberry.experimental.pydantic.type(model=PointLocationBase, all_fields=True)
class PointLocationBaseType:
    pass


@strawberry.experimental.pydantic.input(model=PointLocationBase, all_fields=True)
class PointLocationBaseInput:
    pass


@strawberry.experimental.pydantic.type(model=BrainRegionRead, all_fields=True)
class BrainRegionReadType:
    pass


@strawberry.experimental.pydantic.type(model=StrainRead, all_fields=True)
class StrainReadType:
    pass


@strawberry.experimental.pydantic.type(model=SpeciesRead, all_fields=True)
class SpeciesType:
    pass


@strawberry.experimental.pydantic.input(model=SpeciesCreate, all_fields=True)
class SpeciesInput:
    pass
