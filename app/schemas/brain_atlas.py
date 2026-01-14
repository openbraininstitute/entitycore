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
from app.schemas.species import NestedSpeciesRead
from app.schemas.utils import make_update_schema


class BrainAtlasCreate(AuthorizationOptionalPublicMixin, NameDescriptionMixin):
    model_config = ConfigDict(from_attributes=True)

    hierarchy_id: uuid.UUID
    species_id: uuid.UUID
    strain_id: uuid.UUID | None = None


class BrainAtlasRead(
    AuthorizationMixin,
    CreationMixin,
    CreatedByUpdatedByMixin,
    IdentifiableMixin,
    AssetsMixin,
    NameDescriptionMixin,
):
    model_config = ConfigDict(from_attributes=True)

    hierarchy_id: uuid.UUID
    species: NestedSpeciesRead


BrainAtlasUpdate = make_update_schema(BrainAtlasCreate, "BrainAtlasUpdate")  # pyright: ignore [reportInvalidTypeForm]
BrainAtlasAdminUpdate = make_update_schema(
    BrainAtlasCreate,
    "BrainAtlasAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
