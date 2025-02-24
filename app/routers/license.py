from fastapi import APIRouter

from app.db.model import (
    License,
)
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.base import (
    LicenseCreate,
    LicenseRead,
)

router = APIRouter(
    prefix="/license",
    tags=["license"],
)


@router.get("/", response_model=list[LicenseRead])
def read_licenses(db: SessionDep, skip: int = 0, limit: int = 10):
    return db.query(License).offset(skip).limit(limit).all()


@router.get("/{license_id}", response_model=LicenseRead)
def read_license(license_id: int, db: SessionDep):
    with ensure_result(error_message="License not found"):
        row = db.query(License).filter(License.id == license_id).one()
    return row


@router.post("/", response_model=LicenseRead)
def create_license(license: LicenseCreate, db: SessionDep):
    db_license = License(name=license.name, description=license.description, label=license.label)
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    return db_license
