from app.db.types import CalibrationType
from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate


class CalibrationCreate(ActivityCreate):
    calibration_type: CalibrationType


class CalibrationRead(ActivityRead):
    calibration_type: CalibrationType


class CalibrationUpdate(ActivityUpdate):
    calibration_type: CalibrationType | None = None
