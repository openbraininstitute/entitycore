from fastapi import APIRouter

from app.db.model import MTypeAnnotationBody
from app.dependencies.db import SessionDep
from app.errors import ensure_result
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
    "/{id_}",
    response_model=MTypeRead,
)
def read_mtype(id_: int, db: SessionDep):
    with ensure_result(error_message="mtype not found"):
        mtype = db.query(MTypeAnnotationBody).filter(MTypeAnnotationBody.id == id_).one()

    return MTypeRead.model_validate(mtype)
