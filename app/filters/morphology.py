from datetime import datetime

from fastapi_filter import FilterDepends, with_prefix
from pydantic import field_validator

from app.db.model import ReconstructionMorphology
from app.filters import (
    AgentFilter,
    FilterWithAliases,
    MTypeClassFilter,
    SpeciesFilter,
    StrainFilter,
)


class MorphologyFilter(FilterWithAliases):
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
    contributor: AgentFilter | None = FilterDepends(with_prefix("contributor", AgentFilter))

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(FilterWithAliases.Constants):
        model = ReconstructionMorphology

    # This logic could be in a base class
    @field_validator("order_by")
    @classmethod
    def restrict_sortable_fields(cls, value: list[str]):
        allowed_field_names = ["creation_date", "update_date", "name"]

        for name in value:
            field_name = name.replace("+", "").replace("-", "")
            if field_name not in allowed_field_names:
                msg = f"You may only sort by: {', '.join(allowed_field_names)}"
                raise ValueError(msg)

        return value
