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


class OsInfo(BaseModel):
    """OS information."""

    system: str  # platform.system()
    release: str  # platform.release()
    version: str  # platform.version()
    machine: str  # platform.machine()
    processor: str  # platform.processor()


class PythonInfo(BaseModel):
    """Python runtime information."""

    version: str  # platform.python_version()
    implementation: str  # platform.python_implementation()
    executable: str  # sys.executable


class RuntimeInfo(BaseModel):
    schema_version: int = 1
    os: OsInfo
    python: PythonInfo


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
