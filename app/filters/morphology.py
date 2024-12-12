from pydantic import field_validator
from typing import Optional
from fastapi_filter.contrib.sqlalchemy import Filter
from app.models.morphology import ReconstructionMorphology
from datetime import datetime


class MorphologyFilter(Filter):
    creation_date__lte: Optional[datetime] = None
    creation_date__gte: Optional[datetime] = None
    update_date__lte: Optional[datetime] = None
    update_date__gte: Optional[datetime] = None
    name__ilike: Optional[str] = None
    brain_location_id: Optional[int] = None
    brain_region_id: Optional[int] = None
    species_id__in: Optional[list[int]] = None
    order_by: list[str] = ["-creation_date"]

    class Constants(Filter.Constants):
        model = ReconstructionMorphology

    # This logic could be in a base class
    @field_validator("order_by")
    def restrict_sortable_fields(cls, value: list[str]):
        allowed_field_names = ["creation_date", "update_date", "name"]

        for field_name in value:
            field_name = field_name.replace("+", "").replace("-", "")
            if field_name not in allowed_field_names:
                raise ValueError(
                    f"You may only sort by: {', '.join(allowed_field_names)}"
                )

        return value