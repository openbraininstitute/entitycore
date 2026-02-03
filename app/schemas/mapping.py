import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.base import NameDescriptionMixin
from app.schemas.scientific_artifact import ScientificArtifactCreate, ScientificArtifactRead
from app.schemas.utils import make_update_schema


class MappingBase(BaseModel, NameDescriptionMixin):
    model_config = ConfigDict(from_attributes=True)
    version: str
    source_schema_id: uuid.UUID
    target_schema_id: uuid.UUID


class MappingCreate(
    MappingBase,
    ScientificArtifactCreate,
):
    pass


MappingUserUpdate = make_update_schema(MappingCreate, "MappingUserUpdate")  # pyright: ignore [reportInvalidTypeForm]
MappingAdminUpdate = make_update_schema(
    MappingCreate,
    "MappingAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class MappingRead(
    MappingBase,
    ScientificArtifactRead,
):
    pass
