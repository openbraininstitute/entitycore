import uuid
from typing import Annotated

from fastapi_filter import FilterDepends, with_prefix

from app.db.model import EModel
from app.filters.base import CustomFilter
from app.filters.common import (
    AgentFilter,
    CreationFilterMixin,
    ETypeClassFilter,
    MTypeClassFilter,
    NestedAgentFilterDep,
    NestedETypeClassFilterDep,
    NestedMTypeClassFilterDep,
    NestedSpeciesFilterDep,
    SpeciesFilter,
)
from app.filters.morphology import MorphologyFilter, NestedExemplarMorphologyFilterDep


class EModelFilter(
    CustomFilter,
    CreationFilterMixin,
):
    id__in: list[uuid.UUID] | None = None
    name__ilike: str | None = None
    brain_region_id: int | None = None
    species_id__in: list[uuid.UUID] | None = None

    score__lte: int | None = None
    score__gte: int | None = None

    mtype: Annotated[MTypeClassFilter | None, NestedMTypeClassFilterDep] = None
    etype: Annotated[ETypeClassFilter | None, NestedETypeClassFilterDep] = None
    species: Annotated[SpeciesFilter | None, NestedSpeciesFilterDep] = None
    contribution: Annotated[AgentFilter | None, NestedAgentFilterDep] = None
    exemplar_morphology: Annotated[MorphologyFilter | None, NestedExemplarMorphologyFilterDep] = (
        None
    )

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = EModel
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


# Dependencies
EModelFilterDep = Annotated[EModelFilter, FilterDepends(EModelFilter)]
# Nested dependencies
NestedEModelFilterDep = FilterDepends(with_prefix("emodel", EModelFilter))
