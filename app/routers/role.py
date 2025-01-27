from fastapi import APIRouter, HTTPException

from app.db.model import Role
from app.dependencies.db import SessionDep
from app.schemas.role import RoleCreate, RoleRead

router = APIRouter(
    prefix="/role",
    tags=["role"],
)


@router.get("/{role_id}", response_model=RoleRead)
def read_person(role_id: int, db: SessionDep):
    role = db.query(Role).filter(Role.id == role_id).first()

    if role is None:
        raise HTTPException(status_code=404, detail="role not found")
    ret = RoleRead.model_validate(role)
    return ret


@router.post("/", response_model=RoleRead)
def create_role(role: RoleCreate, db: SessionDep):
    db_role = Role(
        name=role.name,
        role_id=role.role_id,
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return RoleRead.model_validate(db_role)


@router.get("/", response_model=list[RoleRead])
def read_role(db: SessionDep, skip: int = 0, limit: int = 10):
    users = db.query(Role).offset(skip).limit(limit).all()
    return users
