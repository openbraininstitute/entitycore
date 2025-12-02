import uuid

from app.schemas.activity import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    ExecutionActivityMixin,
)
from app.schemas.analysis_notebook_environment import NestedAnalysisNotebookEnvironmentRead
from app.schemas.analysis_notebook_template import NestedAnalysisNotebookTemplateRead
from app.schemas.utils import make_update_schema


class AnalysisNotebookExecutionCreate(ActivityCreate, ExecutionActivityMixin):
    analysis_notebook_template_id: uuid.UUID | None = None
    analysis_notebook_environment_id: uuid.UUID


class AnalysisNotebookExecutionRead(ActivityRead, ExecutionActivityMixin):
    analysis_notebook_template: NestedAnalysisNotebookTemplateRead | None
    analysis_notebook_environment: NestedAnalysisNotebookEnvironmentRead


class AnalysisNotebookExecutionUpdate(ActivityUpdate, ExecutionActivityMixin):
    analysis_notebook_template_id: uuid.UUID | None = None
    analysis_notebook_environment_id: uuid.UUID | None = None


AnalysisNotebookExecutionAdminUpdate = make_update_schema(
    AnalysisNotebookExecutionCreate,
    "AnalysisNotebookExecutionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
