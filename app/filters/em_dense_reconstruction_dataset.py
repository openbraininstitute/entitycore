from typing import Annotated

from app.db.model import EMDenseReconstructionDataset
from app.dependencies.filter import FilterDepends
from app.filters.common import NameFilterMixin
from app.filters.scientific_artifact import ScientificArtifactFilter


class NestedEMDenseReconstructionDatasetFilter(ScientificArtifactFilter, NameFilterMixin):
    class Constants(ScientificArtifactFilter.Constants):
        model = EMDenseReconstructionDataset


class EMDenseReconstructionDatasetFilter(NestedEMDenseReconstructionDatasetFilter):
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(NestedEMDenseReconstructionDatasetFilter.Constants):
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
            "name",
        ]


# Dependencies
EMDenseReconstructionDatasetFilterDep = Annotated[
    EMDenseReconstructionDatasetFilter, FilterDepends(EMDenseReconstructionDatasetFilter)
]
