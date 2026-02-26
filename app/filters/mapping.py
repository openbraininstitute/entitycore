import uuid
from typing import Annotated

from app.db.model import Mapping
from app.dependencies.filter import FilterDepends
from app.filters.common import ILikeSearchFilterMixin, NameFilterMixin
from app.filters.scientific_artifact import ScientificArtifactFilter


class MappingFilter(ScientificArtifactFilter, NameFilterMixin, ILikeSearchFilterMixin):
    version: str | None = None
    source_schema_id: uuid.UUID | None = None
    target_schema_id: uuid.UUID | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(ScientificArtifactFilter.Constants):
        model = Mapping
        ordering_model_fields = ["creation_date", "update_date", "name", "version"]  # noqa: RUF012


MappingFilterDep = Annotated[MappingFilter, FilterDepends(MappingFilter)]
