from fastapi import APIRouter, HTTPException

from app.db.model import WorkflowExecution
from app.dependencies.db import SessionDep
from app.schemas.workflow_execution import WorkflowExecutionCreate, WorkflowExecutionRead

router = APIRouter(
    prefix="/workflow_execution",
    tags=["workflow_execution"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[WorkflowExecutionRead])
def read_workflow_executions(db: SessionDep, skip: int = 0, limit: int = 10):
    return db.query(WorkflowExecution).offset(skip).limit(limit).all()


@router.get("/{workflow_execution_id}", response_model=WorkflowExecutionRead)
def read_workflow_execution(workflow_execution_id: int, db: SessionDep):
    workflow_execution = (
        db.query(WorkflowExecution).filter(WorkflowExecution.id == workflow_execution_id).first()
    )

    if workflow_execution is None:
        raise HTTPException(status_code=404, detail="workflow_execution not found")

    return WorkflowExecutionRead.model_validate(workflow_execution)


@router.post("/", response_model=WorkflowExecutionRead)
def create_workflow_execution(workflow_execution: WorkflowExecutionCreate, db: SessionDep):
    db_workflow_execution = WorkflowExecution(
        name=workflow_execution.name,
        description=workflow_execution.description,
        module=workflow_execution.module,
        task=workflow_execution.task,
        version=workflow_execution.version,
        configFileName=workflow_execution.configFileName,
        status=workflow_execution.status,
    )
    db.add(db_workflow_execution)
    db.commit()
    db.refresh(db_workflow_execution)
    return db_workflow_execution
