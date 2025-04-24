import uuid
from typing import Annotated

from fastapi_filter import FilterDepends, with_prefix

from app.db.model import ReconstructionMorphology
from app.filters.base import CustomFilter
from app.filters.common import (
    AgentFilter,
    CreationFilterMixin,
    MTypeClassFilter,
    NestedAgentFilterDep,
    NestedMTypeClassFilterDep,
    NestedSpeciesFilterDep,
    NestedStrainFilterDep,
    SpeciesFilter,
    StrainFilter,
)


class MorphologyFilter(
    CustomFilter,
    CreationFilterMixin,
):
    id__in: list[uuid.UUID] | None = None
    name__ilike: str | None = None
    brain_region_id: int | None = None
    species_id__in: list[int] | None = None
    mtype: Annotated[MTypeClassFilter | None, NestedMTypeClassFilterDep] = None
    species: Annotated[SpeciesFilter | None, NestedSpeciesFilterDep] = None
    strain: Annotated[StrainFilter | None, NestedStrainFilterDep] = None
    contribution: Annotated[AgentFilter | None, NestedAgentFilterDep] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ReconstructionMorphology
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


# Dependencies
MorphologyFilterDep = Annotated[MorphologyFilter, FilterDepends(MorphologyFilter)]
# Nested dependencies
NestedMorphologyFilterDep = FilterDepends(with_prefix("morphology", MorphologyFilter))
NestedExemplarMorphologyFilterDep = FilterDepends(
    with_prefix("exemplar_morphology", MorphologyFilter)
)
