from app.db.types import JSON_DICT
from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityCreate, NestedEntityRead
from app.schemas.ion_channel_modeling_config import NestedIonChannelModelingConfigRead
from app.schemas.ion_channel_recording import NestedIonChannelRecordingRead
from app.schemas.utils import make_update_schema


class IonChannelModelingCampaignBaseMixin(NameDescriptionMixin):
    scan_parameters: JSON_DICT


class IonChannelModelingCampaignCreate(
    IonChannelModelingCampaignBaseMixin,
    EntityCreate,
):
    input_recordings: list[NestedEntityCreate] = []  # noqa: RUF012


IonChannelModelingCampaignUserUpdate = make_update_schema(
    IonChannelModelingCampaignCreate, "IonChannelModelingCampaignUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]
IonChannelModelingCampaignAdminUpdate = make_update_schema(
    IonChannelModelingCampaignCreate,
    "IonChannelModelingCampaignAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedIonChannelModelingCampaignRead(IonChannelModelingCampaignBaseMixin, NestedEntityRead):
    pass


class IonChannelModelingCampaignRead(
    IonChannelModelingCampaignBaseMixin,
    EntityRead,
):
    input_recordings: list[NestedIonChannelRecordingRead]
    ion_channel_modeling_configs: list[NestedIonChannelModelingConfigRead]
