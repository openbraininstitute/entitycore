import uuid
from typing import Annotated

from app.db.model import MappingRelation
from app.dependencies.filter import FilterDepends
from app.filters.common import ILikeSearchFilterMixin
from app.filters.scientific_artifact import ScientificArtifactFilter


class MappingRelationFilter(ScientificArtifactFilter, ILikeSearchFilterMixin):
    mapping_id: uuid.UUID | None = None
    source_id: uuid.UUID | None = None
    target_id: uuid.UUID | None = None
    parameterisation_relation_id: uuid.UUID | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(ScientificArtifactFilter.Constants):
        model = MappingRelation
        ordering_model_fields = ["creation_date", "update_date"]  # noqa: RUF012


MappingRelationFilterDep = Annotated[MappingRelationFilter, FilterDepends(MappingRelationFilter)]
