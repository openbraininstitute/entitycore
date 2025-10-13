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


class IonChannelModelingBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    ion_channel_modeling_campaign_id: uuid.UUID
    scan_parameters: JSON_DICT


class IonChannelModelingCreate(IonChannelModelingBase, AuthorizationOptionalPublicMixin):
    pass


IonChannelModelingUserUpdate = make_update_schema(
    IonChannelModelingCreate, "IonChannelModelingUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]

IonChannelModelingAdminUpdate = make_update_schema(
    IonChannelModelingCreate,
    "IonChannelModelingAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedIonChannelModelingRead(IonChannelModelingBase, EntityTypeMixin, IdentifiableMixin):
    pass


class IonChannelModelingRead(
    NestedIonChannelModelingRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
):
    pass
