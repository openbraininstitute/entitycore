from pydantic import BaseModel, ConfigDict

from app.db.types import EntityType
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
)
from app.schemas.utils import make_update_schema


class InputType(BaseModel):
    name: str
    type: EntityType
    multiple: bool = False
    count_min: int | None = 1
    count_max: int | None = 1


class Definitions(BaseModel):
    version: int
    inputs: list[InputType]


class AnalysisNotebookTemplateBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    definitions: Definitions | None = None


class AnalysisNotebookTemplateCreate(
    AnalysisNotebookTemplateBase,
    AuthorizationOptionalPublicMixin,
):
    pass


AnalysisNotebookTemplateUpdate = make_update_schema(
    AnalysisNotebookTemplateCreate, "AnalysisNotebookTemplateUpdate"
)  # pyright: ignore [reportInvalidTypeForm]


class NestedAnalysisNotebookTemplateRead(
    AnalysisNotebookTemplateBase,
    EntityTypeMixin,
    IdentifiableMixin,
):
    pass


class AnalysisNotebookTemplateRead(
    NestedAnalysisNotebookTemplateRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
):
    pass
