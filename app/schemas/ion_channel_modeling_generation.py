from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.schemas.utils import make_update_schema


class IonChannelModelingGenerationCreate(ActivityCreate):
    pass


class IonChannelModelingGenerationRead(ActivityRead):
    pass


class IonChannelModelingGenerationUserUpdate(ActivityUpdate):
    pass


IonChannelModelingGenerationAdminUpdate = make_update_schema(
    IonChannelModelingGenerationCreate,
    "IonChannelModelingGenerationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
