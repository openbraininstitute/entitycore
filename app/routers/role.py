from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.role import RoleRead, RoleCreate
from app.dependencies.db import get_db
from app.models.role import Role

router = APIRouter(
    prefix="/role",
    tags=["role"],
)


@router.get(
    "/{role_id}",
    response_model=RoleRead,
)
async def read_person(role_id: int, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()

    if role is None:
        raise HTTPException(status_code=404, detail="role not found")
    ret = RoleRead.model_validate(role)
    return ret


@router.post("/", response_model=RoleRead)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    db_role = Role(
        name=role.name,
        role_id=role.role_id,
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return RoleRead.model_validate(db_role)


@router.get("/", response_model=List[RoleRead])
async def read_role(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(Role).offset(skip).limit(limit).all()
    return users
