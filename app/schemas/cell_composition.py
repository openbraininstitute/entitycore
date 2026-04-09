from uuid import UUID

from pydantic import BaseModel

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
from app.schemas.brain_region import BrainRegionCreateMixin, BrainRegionReadMixin
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.species import NestedSpeciesRead
from app.schemas.utils import make_update_schema


class CellCompositionBase(BaseModel, NameDescriptionMixin):
    pass


class CellCompositionCreate(
    CellCompositionBase, AuthorizationOptionalPublicMixin, BrainRegionCreateMixin
):
    species_id: UUID


CellCompositionUserUpdate = make_update_schema(CellCompositionCreate, "CellCompositionUserUpdate")  # pyright: ignore [reportInvalidTypeForm]
CellCompositionAdminUpdate = make_update_schema(
    CellCompositionCreate,
    "CellCompositionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class CellCompositionRead(
    CellCompositionBase,
    CreationMixin,
    AuthorizationMixin,
    IdentifiableMixin,
    EntityTypeMixin,
    BrainRegionReadMixin,
    CreatedByUpdatedByMixin,
    ContributionReadWithoutEntityMixin,
    AssetsMixin,
):
    species: NestedSpeciesRead
