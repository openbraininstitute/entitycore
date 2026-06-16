import uuid

from app.db.types import JSON_DICT
from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityRead
from app.schemas.utils import make_update_schema


class IonChannelModelingConfigBaseMixin(NameDescriptionMixin):
    ion_channel_modeling_campaign_id: uuid.UUID
    scan_parameters: JSON_DICT


class IonChannelModelingConfigCreate(
    IonChannelModelingConfigBaseMixin,
    EntityCreate,
):
    pass


IonChannelModelingConfigUserUpdate = make_update_schema(
    IonChannelModelingConfigCreate, "IonChannelModelingConfigUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]

IonChannelModelingConfigAdminUpdate = make_update_schema(
    IonChannelModelingConfigCreate,
    "IonChannelModelingConfigAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedIonChannelModelingConfigRead(
    IonChannelModelingConfigBaseMixin,
    NestedEntityRead,
):
    pass


class IonChannelModelingConfigRead(
    IonChannelModelingConfigBaseMixin,
    EntityRead,
):
    pass
