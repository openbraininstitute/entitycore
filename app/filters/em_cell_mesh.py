from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import EMCellMesh
from app.db.types import EMCellMeshType
from app.dependencies.filter import FilterDepends
from app.filters.common import MTypeClassFilterMixin
from app.filters.em_dense_reconstruction_dataset import NestedEMDenseReconstructionDatasetFilter
from app.filters.measurement_annotation import MeasurableFilterMixin
from app.filters.scientific_artifact import ScientificArtifactFilter


class EMCellMeshFilter(
    ScientificArtifactFilter,
    MTypeClassFilterMixin,
    MeasurableFilterMixin,
):
    release_version: int | None = None
    dense_reconstruction_cell_id: int | None = None
    level_of_detail: int | None = None
    mesh_type: EMCellMeshType | None = None

    em_dense_reconstruction_dataset: Annotated[
        NestedEMDenseReconstructionDatasetFilter | None,
        FilterDepends(
            with_prefix(
                "em_dense_reconstruction_dataset",
                NestedEMDenseReconstructionDatasetFilter,
            )
        ),
    ] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(ScientificArtifactFilter.Constants):
        model = EMCellMesh
        ordering_model_fields = [  # noqa: RUF012
            "creation_date",
            "update_date",
        ]


# Dependencies
EMCellMeshFilterDep = Annotated[EMCellMeshFilter, FilterDepends(EMCellMeshFilter)]
