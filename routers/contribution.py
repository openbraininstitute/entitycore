from fastapi import APIRouter
from schemas.contribution import ContributionRead, ContributionCreate
from models.contribution import Contribution
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from models.agent import Agent

from typing import List
from dependencies.db import get_db

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
    )
    db.add(db_contribution)
    db.commit()
    db.refresh(db_contribution)
    print(dir(db_contribution.agent))
    # db_contribution = db.query(Contribution).options(joinedload(Contribution.agent)).get(db_contribution.id)
    return ContributionRead.model_validate(db_contribution)


@router.get("/", response_model=List[ContributionRead])
async def read_contribution(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
):
    users = db.query(Contribution).offset(skip).limit(limit).all()
    return users
