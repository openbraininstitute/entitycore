import uuid

from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.schemas.analysis_notebook_environment import AnalysisNotebookEnvironmentRead
from app.schemas.base import BasicEntityRead


class AnalysisNotebookExecutionCreate(ActivityCreate):
    analysis_notebook_template_id: uuid.UUID | None = None
    analysis_notebook_environment_id: uuid.UUID


class AnalysisNotebookExecutionRead(ActivityRead):
    analysis_notebook_template: BasicEntityRead | None
    analysis_notebook_environment: AnalysisNotebookEnvironmentRead


class AnalysisNotebookExecutionUpdate(ActivityUpdate):
    analysis_notebook_template_id: uuid.UUID | None = None
    analysis_notebook_environment_id: uuid.UUID
