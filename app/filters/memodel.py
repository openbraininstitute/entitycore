from datetime import datetime
from typing import Annotated

from fastapi_filter import FilterDepends, with_prefix

from app.db.model import MEModel, ValidationStatus
from app.filters.base import CustomFilter
from app.filters.common import AgentFilter, ETypeClassFilter, MTypeClassFilter, SpeciesFilter
from app.filters.emodel import EModelFilter
from app.filters.morphology import MorphologyFilter


class MEModelFilter(CustomFilter):
    creation_date__lte: datetime | None = None
    creation_date__gte: datetime | None = None
    update_date__lte: datetime | None = None
    update_date__gte: datetime | None = None
    name__ilike: str | None = None
    brain_region_id: int | None = None
    species_id__in: list[int] | None = None
    validation_status: ValidationStatus | None = None

    mtype: MTypeClassFilter = FilterDepends(with_prefix("mtype", MTypeClassFilter))
    etype: ETypeClassFilter = FilterDepends(with_prefix("etype", ETypeClassFilter))
    species: SpeciesFilter = FilterDepends(with_prefix("species", SpeciesFilter))
    contribution: AgentFilter = FilterDepends(with_prefix("contribution", AgentFilter))
    morphology: MorphologyFilter = FilterDepends(with_prefix("morphology", MorphologyFilter))
    emodel: EModelFilter = FilterDepends(with_prefix("emodel", EModelFilter))

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = MEModel
        ordering_model_fields = ["creation_date", "update_date", "name"]  # noqa: RUF012


MEModelFilterDep = Annotated[MEModelFilter, FilterDepends(MEModelFilter)]
