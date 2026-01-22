import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.parameterisation_relation import NestedParameterisationRelationRead
from app.schemas.scientific_artifact import ScientificArtifactCreate, ScientificArtifactRead
from app.schemas.utils import make_update_schema


class MappingRelationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mapping_id: uuid.UUID
    source_id: uuid.UUID
    target_id: uuid.UUID
    data: Any | None = None
    parameterisation_relation_id: uuid.UUID | None = None


class MappingRelationCreate(
    MappingRelationBase,
    ScientificArtifactCreate,
):
    pass


MappingRelationUserUpdate = make_update_schema(
    MappingRelationCreate,
    "MappingRelationUserUpdate",
)  # pyright: ignore [reportInvalidTypeForm]
MappingRelationAdminUpdate = make_update_schema(
    MappingRelationCreate,
    "MappingRelationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class MappingRelationRead(
    MappingRelationBase,
    ScientificArtifactRead,
):
    parameterisation_relation: NestedParameterisationRelationRead | None = None
