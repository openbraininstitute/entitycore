from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import contains_eager

from app.db.auth import constrain_entity_query_to_project, constrain_to_accessible_entities
from app.db.model import Contribution, Entity
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.db import SessionDep
from app.logger import L
from app.schemas.contribution import ContributionCreate, ContributionRead

router = APIRouter(
    prefix="/contribution",
    tags=["contribution"],
)


@router.get(
    "/{contribution_id}",
    response_model=ContributionRead,
)
def read_contribution(
    contribution_id: int, project_context: VerifiedProjectContextHeader, db: SessionDep
):
    row = (
        db.query(Contribution)
        .filter(Contribution.id == contribution_id)
        .join(Contribution.entity)
        .options(
            contains_eager(Contribution.entity).load_only(
                Entity.authorized_project_id, Entity.authorized_public
            )
        )
        .first()
    )

    if row is None:
        raise HTTPException(status_code=404, detail="contribution not found")

    if (
        not row.entity.authorized_public
        and row.entity.authorized_project_id != project_context.project_id
    ):
        L.warning("Attempting to get an annotation for an entity the user does not have access to")
        raise HTTPException(status_code=404, detail="contribution not found")

    return ContributionRead.model_validate(row)


@router.post("/", response_model=ContributionRead)
def create_contribution(
    contribution: ContributionCreate, project_context: VerifiedProjectContextHeader, db: SessionDep
):
    if not constrain_entity_query_to_project(
        db.query(Entity).filter(Entity.id == contribution.entity_id), project_context.project_id
    ).first():
        L.warning("Attempting to create an annotation for an entity inaccessible to user")
        raise HTTPException(
            status_code=404, detail=f"Cannot access entity {contribution.entity_id}"
        )

    row = Contribution(
        agent_id=contribution.agent_id,
        role_id=contribution.role_id,
        entity_id=contribution.entity_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    result = ContributionRead.model_validate(row)
    return result


@router.get("/", response_model=list[ContributionRead])
def read_contributions(
    project_context: VerifiedProjectContextHeader, db: SessionDep, skip: int = 0, limit: int = 10
):
    return (
        constrain_to_accessible_entities(
            db.query(Contribution).join(Entity), project_context.project_id
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
