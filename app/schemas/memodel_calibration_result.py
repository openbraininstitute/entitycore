import uuid

from pydantic import BaseModel

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
)


class MEModelCalibrationResultBase(BaseModel):
    """Base model for MEModel calibration results."""

    holding_current: float
    threshold_current: float
    rin: float | None = None


class MEModelCalibrationResultRead(MEModelCalibrationResultBase, CreationMixin, IdentifiableMixin, CreatedByUpdatedByMixin):
    """Read model for MEModel calibration results, including entity metadata."""

    calibrated_entity_id: uuid.UUID


class MEModelCalibrationResultCreate(MEModelCalibrationResultBase):
    """Create model for MEModel calibration results."""

    calibrated_entity_id: uuid.UUID
