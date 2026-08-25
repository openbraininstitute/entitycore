from typing import Annotated

from app.db.model import EMDenseReconstructionDataset
from app.dependencies.filter import FilterDepends
from app.filters.common import ILikeSearchFilterMixin, NameFilterMixin
from app.filters.scientific_artifact import NestedScientificArtifactFilter, ScientificArtifactFilter


class NestedEMDenseReconstructionDatasetFilter(
    NestedScientificArtifactFilter,
    NameFilterMixin,
):
    class Constants(NestedScientificArtifactFilter.Constants):
        model = EMDenseReconstructionDataset


class EMDenseReconstructionDatasetFilter(
    ScientificArtifactFilter,
    NameFilterMixin,
    ILikeSearchFilterMixin,
):
    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(ScientificArtifactFilter.Constants):
        model = EMDenseReconstructionDataset
        ordering_model_fields = [  # ruff:ignore[mutable-class-default]
            "creation_date",
            "update_date",
            "name",
        ]


# Dependencies
EMDenseReconstructionDatasetFilterDep = Annotated[
    EMDenseReconstructionDatasetFilter, FilterDepends(EMDenseReconstructionDatasetFilter)
]
