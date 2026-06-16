from pydantic import BaseModel, ConfigDict

from app.schemas.entity import EntityCreate, EntityRead, NestedEntityRead
from app.schemas.types import RuntimeInfo
from app.schemas.utils import make_update_schema


class AnalysisNotebookEnvironmentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    runtime_info: RuntimeInfo | None


class AnalysisNotebookEnvironmentCreate(
    AnalysisNotebookEnvironmentBase,
    EntityCreate,
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
    NestedEntityRead,
):
    pass


class AnalysisNotebookEnvironmentRead(
    AnalysisNotebookEnvironmentBase,
    EntityRead,
):
    pass
