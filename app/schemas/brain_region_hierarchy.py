import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import CreationMixin, IdentifiableMixin
from app.schemas.utils import make_update_schema


class BrainRegionHierarchyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    species_id: uuid.UUID
    strain_id: uuid.UUID | None = None


class BrainRegionHierarchyCreate(BrainRegionHierarchyBase):
    pass


class BrainRegionHierarchyRead(
    BrainRegionHierarchyBase, CreationMixin, CreatedByUpdatedByMixin, IdentifiableMixin
):
    pass


BrainRegionHierarchyAdminUpdate = make_update_schema(
    BrainRegionHierarchyCreate,
    "BrainRegionHierarchyAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
