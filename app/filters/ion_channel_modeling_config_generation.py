from app.db.model import IonChannelModelingConfigGeneration
from app.filters.activity import ActivityFilterMixin
from app.filters.base import CustomFilter


class IonChannelModelingConfigGenerationFilter(CustomFilter, ActivityFilterMixin):
    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = IonChannelModelingConfigGeneration
        ordering_model_fields = ["creation_date", "update_date"]  # ruff:ignore[mutable-class-default]
