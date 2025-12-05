from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.db.types import AnalysisScale, EntityType
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
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.types import DockerDependency, PythonDependency
from app.schemas.utils import make_update_schema


class AnalysisNotebookTemplateInputType(BaseModel):
    """Definition of input types to be used with a notebook template."""

    name: str
    entity_type: EntityType
    is_list: bool = False
    count_min: Annotated[int, Field(ge=0)] = 1
    count_max: Annotated[int | None, Field(ge=0)] = 1


class AnalysisNotebookTemplateSpecifications(BaseModel):
    """Full specifications needed for running a notebook template."""

    schema_version: int = 1
    python: PythonDependency | None = None
    docker: DockerDependency | None = None
    inputs: list[AnalysisNotebookTemplateInputType] = []


class AnalysisNotebookTemplateBase(BaseModel, NameDescriptionMixin):
    model_config = ConfigDict(from_attributes=True)
    specifications: AnalysisNotebookTemplateSpecifications | None = None
    scale: AnalysisScale


class AnalysisNotebookTemplateCreate(
    AnalysisNotebookTemplateBase,
    AuthorizationOptionalPublicMixin,
):
    pass


AnalysisNotebookTemplateUpdate = make_update_schema(
    AnalysisNotebookTemplateCreate, "AnalysisNotebookTemplateUpdate"
)  # pyright: ignore [reportInvalidTypeForm]
AnalysisNotebookTemplateAdminUpdate = make_update_schema(
    AnalysisNotebookTemplateCreate,
    "AnalysisNotebookTemplateAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


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
    ContributionReadWithoutEntityMixin,
):
    pass
