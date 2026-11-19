from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.schemas.base import AuthorizedProjectIdMixin
from app.schemas.utils import make_update_schema


class CalibrationCreate(ActivityCreate):
    pass


class CalibrationAdminCreate(AuthorizedProjectIdMixin, CalibrationCreate):
    pass


class CalibrationRead(ActivityRead):
    pass


class CalibrationUserUpdate(ActivityUpdate):
    pass


CalibrationAdminUpdate = make_update_schema(
    CalibrationCreate,
    "CalibrationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
