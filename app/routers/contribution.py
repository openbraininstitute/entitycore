from fastapi import APIRouter, HTTPException

from app.db.auth import constrain_entity_query_to_project
from app.db.model import Contribution, Entity
from app.dependencies.db import SessionDep
from app.logger import L
from app.routers.auth import AuthProjectContextHeader
from app.schemas.contribution import ContributionCreate, ContributionRead

router = APIRouter(
    prefix="/contribution",
    tags=["contribution"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/{contribution_id}",
    response_model=ContributionRead,
)
def read_contribution(
    contribution_id: int, project_context: AuthProjectContextHeader, db: SessionDep
):

    contribution = db.query(Contribution).filter(Contribution.id == contribution_id).first()

    if contribution is None:
        raise HTTPException(status_code=404, detail="contribution not found")

    return ContributionRead.model_validate(contribution)


@router.post("/", response_model=ContributionRead)
def create_contribution(contribution: ContributionCreate, project_context: AuthProjectContextHeader, db: SessionDep):
    # agent = db.query(Agent).filter(Agent.id == contribution.agent_id).first()
    # if agent is None:
    #     raise HTTPException(status_code=404, detail="Agent not found")
    if not constrain_entity_query_to_project(
        db.query(Entity).filter(Entity.id == contribution.entity_id),
        project_context.project_id
        ).first():
        L.warning("Attempt to access %s", project_context.project_id)
        raise HTTPException(status_code=404, detail=f"Cannot access entity {contribution.entity_id}")

    db_contribution = Contribution(
        agent_id=contribution.agent_id,
        role_id=contribution.role_id,
        entity_id=contribution.entity_id,
    )
    db.add(db_contribution)
    db.commit()
    db.refresh(db_contribution)
    return ContributionRead.model_validate(db_contribution)


@router.get("/", response_model=list[ContributionRead])
def read_contributions(project_context: AuthProjectContextHeader, db: SessionDep, skip: int = 0, limit: int = 10):
    return db.query(Contribution).offset(skip).limit(limit).all()
