from datetime import datetime

from fastapi_filter import FilterDepends, with_prefix

from app.db.model import ReconstructionMorphology
from app.filters.base import CustomFilter
from app.filters.common import AgentFilter, MTypeClassFilter, SpeciesFilter, StrainFilter


class MorphologyFilter(CustomFilter):
    creation_date__lte: datetime | None = None
    creation_date__gte: datetime | None = None
    update_date__lte: datetime | None = None
    update_date__gte: datetime | None = None
    name__ilike: str | None = None
    brain_location_id: int | None = None
    brain_region_id: int | None = None
    species_id__in: list[int] | None = None

    mtype: MTypeClassFilter | None = FilterDepends(with_prefix("mtype", MTypeClassFilter))
    species: SpeciesFilter | None = FilterDepends(with_prefix("species", SpeciesFilter))
    strain: StrainFilter | None = FilterDepends(with_prefix("strain", StrainFilter))
    contribution: AgentFilter | None = FilterDepends(with_prefix("contribution", AgentFilter))

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ReconstructionMorphology
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
            "mtype",
            "strain",
            "species",
        ]
