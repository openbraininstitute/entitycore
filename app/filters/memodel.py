from typing import Annotated

from fastapi_filter import FilterDepends, with_prefix

from app.db.model import MEModel, ValidationStatus
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
from app.filters.emodel import EModelFilter, NestedEModelFilterDep
from app.filters.morphology import MorphologyFilter, NestedMorphologyFilterDep


class MEModelFilter(
    CustomFilter,
    CreationFilterMixin,
):
    name__ilike: str | None = None
    brain_region_id: int | None = None
    species_id__in: list[int] | None = None
    validation_status: ValidationStatus | None = None

    mtype: Annotated[MTypeClassFilter | None, NestedMTypeClassFilterDep] = None
    etype: Annotated[ETypeClassFilter | None, NestedETypeClassFilterDep] = None
    species: Annotated[SpeciesFilter | None, NestedSpeciesFilterDep] = None
    contribution: Annotated[AgentFilter | None, NestedAgentFilterDep] = None
    morphology: Annotated[MorphologyFilter | None, NestedMorphologyFilterDep] = None
    emodel: Annotated[EModelFilter | None, NestedEModelFilterDep] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = MEModel
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


# Dependencies
MEModelFilterDep = Annotated[MEModelFilter, FilterDepends(MEModelFilter)]
# Nested dependencies
NestedMEModelFilterDep = FilterDepends(with_prefix("me_type", MEModelFilter))
