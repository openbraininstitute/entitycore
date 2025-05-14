import uuid

from fastapi import APIRouter

import app.service.electrical_cell_recording
import app.service.emodel
from app.dependencies.auth import UserContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.electrical_cell_recording import ElectricalCellRecordingFilter
from app.schemas.electrical_cell_recording import ElectricalCellRecordingRead
from app.schemas.types import ListResponse

router = APIRouter(
    prefix="/emodel",
    tags=["emodel"],
)

read_many = router.get("")(app.service.emodel.read_many)
read_one = router.get("/{id_}")(app.service.emodel.read_one)
create_one = router.post("")(app.service.emodel.create_one)


@router.get("/{id_}/electrical-cell-recording")
def get_electrical_cell_recording(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    pagination_request: PaginationQuery,
) -> ListResponse[ElectricalCellRecordingRead]:
    """Return the list of ElectricalCellRecording used to generate the specified EModel."""
    filter_model = ElectricalCellRecordingFilter.model_validate({"generated_emodel": {"id": id_}})
    return app.service.electrical_cell_recording.read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=None,
        facets=None,
        in_brain_region=None,
    )
