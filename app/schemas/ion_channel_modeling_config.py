import uuid

from pydantic import BaseModel, ConfigDict

from app.db.types import JSON_DICT
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
)
from app.schemas.utils import make_update_schema


class IonChannelModelingConfigBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    ion_channel_modeling_campaign_id: uuid.UUID
    scan_parameters: JSON_DICT


class IonChannelModelingConfigCreate(
    IonChannelModelingConfigBase, AuthorizationOptionalPublicMixin
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
    IonChannelModelingConfigBase, EntityTypeMixin, IdentifiableMixin
):
    pass


class IonChannelModelingConfigRead(
    NestedIonChannelModelingConfigRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
):
    pass
