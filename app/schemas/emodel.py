import uuid
from typing import Annotated

from pydantic import Field

from app.schemas.annotation import ETypeClassRead, MTypeClassRead
from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.brain_region import BrainRegionCreateMixin, BrainRegionReadMixin
from app.schemas.cell_morphology import CellMorphologyBaseMixin
from app.schemas.cell_morphology_protocol import NestedCellMorphologyProtocolRead
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityCreate
from app.schemas.identifiable import NestedIdentifiableRead
from app.schemas.ion_channel_model import IonChannelModelWAssets
from app.schemas.species import SpeciesStrainCreateMixin, SpeciesStrainReadMixin
from app.schemas.utils import make_update_schema


class ExemplarMorphology(CellMorphologyBaseMixin, NestedIdentifiableRead):
    cell_morphology_protocol: NestedCellMorphologyProtocolRead


class EModelBaseMixin(NameDescriptionMixin):
    iteration: str
    score: float
    seed: int


class EModelCreate(EModelBaseMixin, EntityCreate, SpeciesStrainCreateMixin, BrainRegionCreateMixin):
    exemplar_morphology_id: uuid.UUID
    ion_channel_models: Annotated[
        list[NestedEntityCreate],
        Field(description="List of ion channel models (only ids)."),
    ] = []  # noqa: RUF012


EModelUserUpdate = make_update_schema(EModelCreate, "EModelUserUpdate")  # pyright: ignore [reportInvalidTypeForm]
EModelAdminUpdate = make_update_schema(
    EModelCreate,
    "EModelAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class EModelRead(
    EModelBaseMixin,
    EntityRead,
    BrainRegionReadMixin,
    SpeciesStrainReadMixin,
):
    mtypes: list[MTypeClassRead] | None
    etypes: list[ETypeClassRead] | None
    exemplar_morphology: ExemplarMorphology


class EModelReadExpanded(EModelRead):
    ion_channel_models: list[IonChannelModelWAssets]
