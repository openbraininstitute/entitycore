import uuid

from pydantic import ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    IdentifiableMixin,
    NameDescriptionMixin,
)
from app.schemas.species import SpeciesStrainCreateMixin, SpeciesStrainReadMixin
from app.schemas.utils import make_update_schema


class BrainAtlasCreate(
    AuthorizationOptionalPublicMixin, NameDescriptionMixin, SpeciesStrainCreateMixin
):
    model_config = ConfigDict(from_attributes=True)

    hierarchy_id: uuid.UUID


class BrainAtlasRead(
    AuthorizationMixin,
    CreationMixin,
    CreatedByUpdatedByMixin,
    IdentifiableMixin,
    AssetsMixin,
    NameDescriptionMixin,
    SpeciesStrainReadMixin,
):
    model_config = ConfigDict(from_attributes=True)

    hierarchy_id: uuid.UUID


BrainAtlasUpdate = make_update_schema(BrainAtlasCreate, "BrainAtlasUpdate")  # pyright: ignore [reportInvalidTypeForm]
BrainAtlasAdminUpdate = make_update_schema(
    BrainAtlasCreate,
    "BrainAtlasAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
