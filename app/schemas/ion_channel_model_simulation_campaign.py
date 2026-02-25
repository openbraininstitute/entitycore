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
    NameDescriptionMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.ion_channel import NestedIonChannelRead
from app.schemas.utils import make_update_schema


class IonChannelModelSimulationCampaignBase(BaseModel, NameDescriptionMixin):
    model_config = ConfigDict(from_attributes=True)
    scan_parameters: JSON_DICT


class IonChannelModelSimulationCampaignCreate(
    IonChannelModelSimulationCampaignBase, AuthorizationOptionalPublicMixin
):
    pass


IonChannelModelSimulationCampaignUserUpdate = make_update_schema(
    IonChannelModelSimulationCampaignCreate, "IonChannelModelSimulationCampaignUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]
IonChannelModelSimulationCampaignAdminUpdate = make_update_schema(
    IonChannelModelSimulationCampaignCreate,
    "IonChannelModelSimulationCampaignAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedIonChannelModelSimulationCampaignRead(
    IonChannelModelSimulationCampaignBase, EntityTypeMixin, IdentifiableMixin
):
    pass


class IonChannelModelSimulationCampaignRead(
    NestedIonChannelModelSimulationCampaignRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
    ContributionReadWithoutEntityMixin,
):
    ion_channel_models: list[NestedIonChannelRead]
