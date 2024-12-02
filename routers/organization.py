from fastapi import APIRouter
from schemas.agent import OrganizationRead, OrganizationCreate
from models.agent import Organization
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from typing import List
from dependencies.db import get_db

router = APIRouter(
    prefix="/organization",
    tags=["organization"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/{organization_id}",
    response_model=OrganizationRead,
)
async def read_organization(organization_id: int, db: Session = Depends(get_db)):
    organization = db.query(Organization).filter(Organization.id == organization_id).first()

    if organization is None:
        raise HTTPException(status_code=404, detail="organization not found")
    ret = OrganizationRead.model_validate(organization)
    return ret


@router.post("/", response_model=OrganizationRead)
def create_organization(organization: OrganizationCreate, db: Session = Depends(get_db)):
    db_organization = Organization(**organization.model_dump())
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    return db_organization


@router.get("/", response_model=List[OrganizationRead])
async def read_organization(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(Organization).offset(skip).limit(limit).all()
    return users
