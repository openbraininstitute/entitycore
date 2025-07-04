import uuid

from pydantic import BaseModel

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    IdentifiableMixin,
)


class MEModelCalibrationResultBase(BaseModel):
    """Base model for MEModel calibration results."""

    holding_current: float
    threshold_current: float
    rin: float | None = None
    calibrated_entity_id: uuid.UUID


class MEModelCalibrationResultRead(
    MEModelCalibrationResultBase,
    CreationMixin,
    IdentifiableMixin,
    CreatedByUpdatedByMixin,
    AuthorizationMixin,
):
    """Read model for MEModel calibration results, including entity metadata."""


class MEModelCalibrationResultCreate(
    MEModelCalibrationResultBase, AuthorizationOptionalPublicMixin
):
    """Create model for MEModel calibration results."""
