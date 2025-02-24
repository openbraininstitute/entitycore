from fastapi import APIRouter

from app.db.model import Person
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.agent import PersonCreate, PersonRead

router = APIRouter(
    prefix="/person",
    tags=["person"],
)


@router.get("/", response_model=list[PersonRead])
def read_persons(db: SessionDep, skip: int = 0, limit: int = 10):
    return db.query(Person).offset(skip).limit(limit).all()


@router.get("/{person_id}", response_model=PersonRead)
def read_person(person_id: int, db: SessionDep):
    with ensure_result(error_message="Person not found"):
        row = db.query(Person).filter(Person.id == person_id).one()

    return row


@router.post("/", response_model=PersonRead)
def create_person(person: PersonCreate, db: SessionDep):
    db_person = Person(**person.model_dump())
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person
