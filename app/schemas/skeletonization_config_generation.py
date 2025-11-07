from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.schemas.utils import make_update_schema


class SkeletonizationConfigGenerationCreate(ActivityCreate):
    pass


class SkeletonizationConfigGenerationRead(ActivityRead):
    pass


class SkeletonizationConfigGenerationUserUpdate(ActivityUpdate):
    pass


SkeletonizationConfigGenerationAdminUpdate = make_update_schema(
    SkeletonizationConfigGenerationCreate,
    "SkeletonizationConfigGenerationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
