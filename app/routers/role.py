from fastapi import APIRouter

from app.db.model import Role
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.role import RoleCreate, RoleRead

router = APIRouter(
    prefix="/role",
    tags=["role"],
)


@router.get("/", response_model=list[RoleRead])
def read_role(db: SessionDep, skip: int = 0, limit: int = 10):
    return db.query(Role).offset(skip).limit(limit).all()


@router.get("/{role_id}", response_model=RoleRead)
def read_person(role_id: int, db: SessionDep):
    with ensure_result(error_message="Role not found"):
        row = db.query(Role).filter(Role.id == role_id).one()
    return row


@router.post("/", response_model=RoleRead)
def create_role(role: RoleCreate, db: SessionDep):
    db_role = Role(
        name=role.name,
        role_id=role.role_id,
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role
