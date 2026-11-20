from app.db.model import GenericDataset
from app.filters.base import CustomFilter
from app.filters.brain_region import BrainRegionFilterMixin
from app.filters.common import ILikeSearchFilterMixin, NameFilterMixin
from app.filters.entity import EntityFilterMixin
from app.filters.subject import SubjectFilterMixin


class GenericDatasetFilter(
    SubjectFilterMixin,
    BrainRegionFilterMixin,
    EntityFilterMixin,
    NameFilterMixin,
    ILikeSearchFilterMixin,
    CustomFilter,
):
    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = GenericDataset
        ordering_model_fields = [  # ruff:ignore[mutable-class-default]
            "creation_date",
            "update_date",
            "name",
            "subject__species__name",
            "brain_region__acronym",
            "brain_region__name",
        ]
