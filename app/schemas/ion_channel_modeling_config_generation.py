from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.schemas.utils import make_update_schema


class IonChannelModelingConfigGenerationCreate(ActivityCreate):
    pass


class IonChannelModelingConfigGenerationRead(ActivityRead):
    pass


class IonChannelModelingConfigGenerationUserUpdate(ActivityUpdate):
    pass


IonChannelModelingConfigGenerationAdminUpdate = make_update_schema(
    IonChannelModelingConfigGenerationCreate,
    "IonChannelModelingConfigGenerationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
