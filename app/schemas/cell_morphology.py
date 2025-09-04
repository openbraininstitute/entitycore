import uuid

from pydantic import BaseModel, ConfigDict

from app.db.types import (
    PointLocationBase,
)
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.annotation import MTypeClassRead
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionReadMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    LicensedCreateMixin,
    LicensedReadMixin,
)
from app.schemas.cell_morphology_protocol import NestedCellMorphologyProtocolRead
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.measurement_annotation import MeasurementAnnotationRead
from app.schemas.subject import SubjectReadMixin


class CellMorphologyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    location: PointLocationBase | None
    legacy_id: list[str] | None = None


class CellMorphologyCreate(
    CellMorphologyBase,
    LicensedCreateMixin,
    AuthorizationOptionalPublicMixin,
):
    subject_id: uuid.UUID
    brain_region_id: uuid.UUID
    cell_morphology_protocol_id: uuid.UUID | None = None


class CellMorphologyRead(
    CellMorphologyBase,
    CreationMixin,
    IdentifiableMixin,
    LicensedReadMixin,
    AuthorizationMixin,
    AssetsMixin,
    EntityTypeMixin,
    CreatedByUpdatedByMixin,
    ContributionReadWithoutEntityMixin,
    SubjectReadMixin,
    BrainRegionReadMixin,
):
    mtypes: list[MTypeClassRead] | None
    cell_morphology_protocol: NestedCellMorphologyProtocolRead | None


class CellMorphologyAnnotationExpandedRead(CellMorphologyRead):
    measurement_annotation: MeasurementAnnotationRead | None
