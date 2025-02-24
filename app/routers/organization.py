from fastapi import APIRouter

from app.db.model import Organization
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.agent import OrganizationCreate, OrganizationRead

router = APIRouter(
    prefix="/organization",
    tags=["organization"],
)


@router.get("/", response_model=list[OrganizationRead])
def read_organizations(db: SessionDep, skip: int = 0, limit: int = 10):
    return db.query(Organization).offset(skip).limit(limit).all()


@router.get("/{organization_id}", response_model=OrganizationRead)
def read_organization(organization_id: int, db: SessionDep):
    with ensure_result(error_message="Organization not found"):
        row = db.query(Organization).filter(Organization.id == organization_id).one()
    return row


@router.post("/", response_model=OrganizationRead)
def create_organization(organization: OrganizationCreate, db: SessionDep):
    db_organization = Organization(**organization.model_dump())
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    return db_organization
