from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

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


class PythonDependency(BaseModel):
    version: str  # e.g. ">=3.10,<3.12"


class InputType(BaseModel):
    name: str
    type: EntityType
    is_list: bool = False
    count_min: Annotated[int, Field(ge=0)] = 1
    count_max: Annotated[int | None, Field(ge=0)] = 1


class Specifications(BaseModel):
    schema_version: int = 1
    python: PythonDependency
    inputs: list[InputType]


class AnalysisNotebookTemplateBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    specifications: Specifications | None = None


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
