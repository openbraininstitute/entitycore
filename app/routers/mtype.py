from fastapi import APIRouter, HTTPException

from app.db.model import MTypeAnnotationBody
from app.dependencies.db import SessionDep
from app.schemas.mtype import MTypeRead

router = APIRouter(
    prefix="/mtype",
    tags=["mtype"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[MTypeRead])
def read_mtypes(db: SessionDep, skip: int = 0, limit: int = 10):
    return db.query(MTypeAnnotationBody).offset(skip).limit(limit).all()


@router.get(
    "/{mtype_id}",
    response_model=MTypeRead,
)
def read_mtype(mtype_id: int, db: SessionDep):
    mtype = db.query(MTypeAnnotationBody).filter(MTypeAnnotationBody.id == mtype_id).first()

    if mtype is None:
        raise HTTPException(status_code=404, detail="mtype not found")

    return MTypeRead.model_validate(mtype)
