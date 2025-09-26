from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
)
from app.schemas.types import RuntimeInfo
from app.schemas.utils import make_update_schema


class AnalysisNotebookEnvironmentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    runtime_info: RuntimeInfo | None


class AnalysisNotebookEnvironmentCreate(
    AnalysisNotebookEnvironmentBase,
    AuthorizationOptionalPublicMixin,
):
    pass


AnalysisNotebookEnvironmentUpdate = make_update_schema(
    AnalysisNotebookEnvironmentCreate, "AnalysisNotebookEnvironmentUpdate"
)  # pyright: ignore [reportInvalidTypeForm]
AnalysisNotebookEnvironmentAdminUpdate = make_update_schema(
    AnalysisNotebookEnvironmentCreate,
    "AnalysisNotebookEnvironmentAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedAnalysisNotebookEnvironmentRead(
    AnalysisNotebookEnvironmentBase,
    EntityTypeMixin,
    IdentifiableMixin,
):
    pass


class AnalysisNotebookEnvironmentRead(
    NestedAnalysisNotebookEnvironmentRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
):
    pass
