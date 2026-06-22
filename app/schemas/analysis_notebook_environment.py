from app.schemas.entity import EntityCreate, EntityRead, NestedEntityRead
from app.schemas.types import RuntimeInfo
from app.schemas.utils import make_update_schema


class AnalysisNotebookEnvironmentBaseMixin:
    runtime_info: RuntimeInfo | None


class AnalysisNotebookEnvironmentCreate(
    AnalysisNotebookEnvironmentBaseMixin,
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
    AnalysisNotebookEnvironmentBaseMixin,
    NestedEntityRead,
):
    pass


class AnalysisNotebookEnvironmentRead(
    AnalysisNotebookEnvironmentBaseMixin,
    EntityRead,
):
    pass
