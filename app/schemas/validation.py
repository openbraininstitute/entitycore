import uuid

from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.schemas.entity import EntityCreate, EntityRead
from app.schemas.utils import make_update_schema


class ValidationCreate(ActivityCreate):
    pass


class ValidationRead(ActivityRead):
    pass


class ValidationUserUpdate(ActivityUpdate):
    pass


class ValidationResultBaseMixin:
    name: str
    passed: bool
    validated_entity_id: uuid.UUID


class ValidationResultRead(
    ValidationResultBaseMixin,
    EntityRead,
):
    pass


class ValidationResultCreate(ValidationResultBaseMixin, EntityCreate):
    pass


ValidationResultUserUpdate = make_update_schema(
    ValidationResultCreate, "ValidationResultUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]

ValidationResultAdminUpdate = make_update_schema(
    ValidationResultCreate,
    "ValidationResultAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]

ValidationAdminUpdate = make_update_schema(
    ValidationCreate,
    "ValidationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
