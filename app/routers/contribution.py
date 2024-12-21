from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.models.contribution import Contribution
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
async def read_contribution(contribution_id: int, db: Session = Depends(get_db)):
    contribution = (
        db.query(Contribution).filter(Contribution.id == contribution_id).first()
    )

    if contribution is None:
        raise HTTPException(status_code=404, detail="contribution not found")
    ret = ContributionRead.model_validate(contribution)
    return ret


@router.post("/", response_model=ContributionRead)
def create_contribution(
    contribution: ContributionCreate, db: Session = Depends(get_db)
):
    # agent = db.query(Agent).filter(Agent.id == contribution.agent_id).first()
    # if agent is None:
    #     raise HTTPException(status_code=404, detail="Agent not found")

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
async def read_contributions(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
):
    users = db.query(Contribution).offset(skip).limit(limit).all()
    return users
