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


@router.get("/{id_}", response_model=OrganizationRead)
def read_organization(id_: int, db: SessionDep):
    with ensure_result(error_message="Organization not found"):
        row = db.query(Organization).filter(Organization.id == id_).one()
    return OrganizationRead.model_validate(row)


@router.post("/", response_model=OrganizationRead)
def create_organization(organization: OrganizationCreate, db: SessionDep):
    row = Organization(**organization.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
