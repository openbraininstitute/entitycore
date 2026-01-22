from typing import Annotated

from app.db.model import ParameterisationRelation
from app.dependencies.filter import FilterDepends
from app.filters.common import ILikeSearchFilterMixin
from app.filters.scientific_artifact import ScientificArtifactFilter


class ParameterisationRelationFilter(ScientificArtifactFilter, ILikeSearchFilterMixin):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(ScientificArtifactFilter.Constants):
        model = ParameterisationRelation
        ordering_model_fields = ["creation_date", "update_date"]  # noqa: RUF012


ParameterisationRelationFilterDep = Annotated[
    ParameterisationRelationFilter,
    FilterDepends(ParameterisationRelationFilter),
]
