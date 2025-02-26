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
def read_roles(db: SessionDep, skip: int = 0, limit: int = 10):
    return db.query(Role).offset(skip).limit(limit).all()


@router.get("/{id_}", response_model=RoleRead)
def read_role(id_: int, db: SessionDep):
    with ensure_result(error_message="Role not found"):
        row = db.query(Role).filter(Role.id == id_).one()
    return RoleRead.model_validate(row)


@router.post("/", response_model=RoleRead)
def create_role(role: RoleCreate, db: SessionDep):
    row = Role(name=role.name, role_id=role.role_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
