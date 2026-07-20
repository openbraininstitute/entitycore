from typing import Annotated

from pydantic import Field

from app.db.types import AnalysisScale, EntityType
from app.schemas.base import (
    NameDescriptionMixin,
    Schema,
)
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityRead
from app.schemas.types import DockerDependency, PythonDependency
from app.schemas.utils import make_update_schema


class AnalysisNotebookTemplateInputType(Schema):
    """Definition of input types to be used with a notebook template."""

    name: str
    entity_type: EntityType
    is_list: bool = False
    count_min: Annotated[int, Field(ge=0)] = 1
    count_max: Annotated[int | None, Field(ge=0)] = 1


class AnalysisNotebookTemplateSpecifications(Schema):
    """Full specifications needed for running a notebook template."""

    schema_version: int = 1
    python: PythonDependency | None = None
    docker: DockerDependency | None = None
    inputs: list[AnalysisNotebookTemplateInputType] = []  # ruff:ignore[mutable-class-default]


class AnalysisNotebookTemplateBaseMixin(NameDescriptionMixin):
    specifications: AnalysisNotebookTemplateSpecifications | None = None
    scale: AnalysisScale
    assignment_id: Annotated[str | None, Field(min_length=1, max_length=255)] = None


class AnalysisNotebookTemplateCreate(
    AnalysisNotebookTemplateBaseMixin,
    EntityCreate,
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
    AnalysisNotebookTemplateBaseMixin,
    NestedEntityRead,
):
    pass


class AnalysisNotebookTemplateRead(
    AnalysisNotebookTemplateBaseMixin,
    EntityRead,
):
    pass
