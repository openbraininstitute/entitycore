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
from app.schemas.simulation import NestedSimulationRead
from app.schemas.utils import make_update_schema


class IonChannelModelingCampaignBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    scan_parameters: JSON_DICT


class IonChannelModelingCampaignCreate(IonChannelModelingCampaignBase, AuthorizationOptionalPublicMixin):
    pass


IonChannelModelingCampaignUserUpdate = make_update_schema(
    IonChannelModelingCampaignCreate, "IonChannelModelingCampaignUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]
IonChannelModelingCampaignAdminUpdate = make_update_schema(
    IonChannelModelingCampaignCreate,
    "IonChannelModelingCampaignAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedIonChannelModelingCampaignRead(IonChannelModelingCampaignBase, EntityTypeMixin, IdentifiableMixin):
    pass


class IonChannelModelingCampaignRead(
    NestedIonChannelModelingCampaignRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
):
    ion_channel_modelings: list[NestedIonChannelModelingRead]
