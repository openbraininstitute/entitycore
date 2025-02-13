from pydantic import BaseModel, ConfigDict

from app.schemas.base import CreationMixin


class WorkflowExecutionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str

    module: str
    task: str
    version: str

    configFileName: str

    status: str


class WorkflowExecutionRead(WorkflowExecutionBase, CreationMixin):
    """Workflow execution read schema."""

    id: int


class WorkflowExecutionCreate(WorkflowExecutionBase):
    """Workflow execution creation schema."""
