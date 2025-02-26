from fastapi import APIRouter

from app.db.model import License
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.base import LicenseCreate, LicenseRead

router = APIRouter(
    prefix="/license",
    tags=["license"],
)


@router.get("/", response_model=list[LicenseRead])
def read_licenses(db: SessionDep, skip: int = 0, limit: int = 10):
    return db.query(License).offset(skip).limit(limit).all()


@router.get("/{id_}", response_model=LicenseRead)
def read_license(id_: int, db: SessionDep):
    with ensure_result(error_message="License not found"):
        row = db.query(License).filter(License.id == id_).one()
    return LicenseRead.model_validate(row)


@router.post("/", response_model=LicenseRead)
def create_license(license: LicenseCreate, db: SessionDep):
    row = License(name=license.name, description=license.description, label=license.label)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
