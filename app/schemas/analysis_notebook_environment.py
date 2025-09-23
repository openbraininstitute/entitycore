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
from app.schemas.utils import make_update_schema


class Runtime(BaseModel):
    os: dict[str, str]  # Expected: platform.uname()._asdict()
    python_version: str  # Expected: sys.version


class AnalysisNotebookEnvironmentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    runtime: Runtime | None


class AnalysisNotebookEnvironmentCreate(
    AnalysisNotebookEnvironmentBase,
    AuthorizationOptionalPublicMixin,
):
    pass


AnalysisNotebookEnvironmentUpdate = make_update_schema(
    AnalysisNotebookEnvironmentCreate, "AnalysisNotebookEnvironmentUpdate"
)  # pyright: ignore [reportInvalidTypeForm]


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
