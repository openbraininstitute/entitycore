import uuid

from pydantic import BaseModel

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.entity import EntityCreate, EntityReadWoutAssets, NestedEntityRead
from app.schemas.utils import make_update_schema


class MEModelCalibrationResultBase(BaseModel):
    """Base model for MEModel calibration results."""

    holding_current: float
    threshold_current: float
    rin: float | None = None
    calibrated_entity_id: uuid.UUID


class NestedMEModelCalibrationResultRead(
    MEModelCalibrationResultBase,
    NestedEntityRead,
    CreatedByUpdatedByMixin,
):
    pass


class MEModelCalibrationResultRead(
    MEModelCalibrationResultBase,
    EntityReadWoutAssets,
):
    """Read model for MEModel calibration results, including entity metadata."""


class MEModelCalibrationResultCreate(
    MEModelCalibrationResultBase,
    EntityCreate,
):
    """Create model for MEModel calibration results."""


MEModelCalibrationResultUserUpdate = make_update_schema(
    MEModelCalibrationResultCreate, "MEModelCalibrationResultUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]
MEModelCalibrationResultAdminUpdate = make_update_schema(
    MEModelCalibrationResultCreate,
    "MEModelCalibrationResultAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
