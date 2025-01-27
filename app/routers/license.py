from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.model import (
    License,
)
from app.dependencies.db import get_db
from app.schemas.base import (
    LicenseCreate,
    LicenseRead,
)

router = APIRouter(
    prefix="/license",
    tags=["license"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[LicenseRead])
def read_licenses(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(License).offset(skip).limit(limit).all()
    return users


@router.get("/{license_id}", response_model=LicenseRead)
def read_license(license_id: int, db: Session = Depends(get_db)):
    license = db.query(License).filter(License.id == license_id).first()
    if license is None:
        raise HTTPException(status_code=404, detail="License not found")
    return license


@router.post("/", response_model=LicenseRead)
def create_license(license: LicenseCreate, db: Session = Depends(get_db)):
    db_license = License(
        name=license.name, description=license.description, label=license.label
    )
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    return db_license
