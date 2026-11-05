from app.db.model import Asset
from app.filters.base import CustomFilter


class AssetFilter(CustomFilter):
    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = Asset
        ordering_model_fields = ["creation_date"]  # ruff:ignore[mutable-class-default]
