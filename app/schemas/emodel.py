import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.annotation import ETypeClassRead, MTypeClassRead
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    NameDescriptionMixin,
)
from app.schemas.brain_region import BrainRegionReadMixin
from app.schemas.cell_morphology import CellMorphologyBase
from app.schemas.cell_morphology_protocol import NestedCellMorphologyProtocolRead
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.entity import NestedEntityCreate
from app.schemas.ion_channel_model import IonChannelModelWAssets
from app.schemas.species import SpeciesStrainCreateMixin, SpeciesStrainReadMixin
from app.schemas.utils import make_update_schema


class ExemplarMorphology(CreationMixin, CellMorphologyBase, IdentifiableMixin):
    cell_morphology_protocol: NestedCellMorphologyProtocolRead


class EModelBase(BaseModel, NameDescriptionMixin):
    model_config = ConfigDict(from_attributes=True)
    iteration: str
    score: float
    seed: int


class EModelCreate(EModelBase, AuthorizationOptionalPublicMixin, SpeciesStrainCreateMixin):
    brain_region_id: uuid.UUID
    exemplar_morphology_id: uuid.UUID
    ion_channel_models: Annotated[
        list[NestedEntityCreate],
        Field(description="List of ion channel models (only ids)."),
    ] = []


EModelUserUpdate = make_update_schema(EModelCreate, "EModelUserUpdate")  # pyright: ignore [reportInvalidTypeForm]
EModelAdminUpdate = make_update_schema(
    EModelCreate,
    "EModelAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class EModelRead(
    EModelBase,
    CreationMixin,
    AuthorizationMixin,
    EntityTypeMixin,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    ContributionReadWithoutEntityMixin,
    BrainRegionReadMixin,
    SpeciesStrainReadMixin,
):
    id: uuid.UUID
    mtypes: list[MTypeClassRead] | None
    etypes: list[ETypeClassRead] | None
    exemplar_morphology: ExemplarMorphology


class EModelReadExpanded(EModelRead, AssetsMixin):
    ion_channel_models: list[IonChannelModelWAssets]
