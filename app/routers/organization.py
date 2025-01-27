from fastapi import APIRouter, HTTPException

from app.db.model import Organization
from app.dependencies.db import SessionDep
from app.schemas.agent import OrganizationCreate, OrganizationRead

router = APIRouter(
    prefix="/organization",
    tags=["organization"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{organization_id}", response_model=OrganizationRead)
def read_organization(organization_id: int, db: SessionDep):
    organization = db.query(Organization).filter(Organization.id == organization_id).first()

    if organization is None:
        raise HTTPException(status_code=404, detail="organization not found")
    ret = OrganizationRead.model_validate(organization)
    return ret


@router.post("/", response_model=OrganizationRead)
def create_organization(organization: OrganizationCreate, db: SessionDep):
    db_organization = Organization(**organization.model_dump())
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    return db_organization


@router.get("/", response_model=list[OrganizationRead])
def read_organizations(db: SessionDep, skip: int = 0, limit: int = 10):
    users = db.query(Organization).offset(skip).limit(limit).all()
    return users
