from fastapi import APIRouter, HTTPException

from app.db.model import Person
from app.dependencies.db import SessionDep
from app.schemas.agent import PersonCreate, PersonRead

router = APIRouter(
    prefix="/person",
    tags=["person"],
)


@router.get("/{person_id}", response_model=PersonRead)
def read_person(person_id: int, db: SessionDep):
    person = db.query(Person).filter(Person.id == person_id).first()

    if person is None:
        raise HTTPException(status_code=404, detail="person not found")
    return PersonRead.model_validate(person)


@router.post("/", response_model=PersonRead)
def create_person(person: PersonCreate, db: SessionDep):
    db_person = Person(**person.model_dump())
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person


@router.get("/", response_model=list[PersonRead])
def read_persons(db: SessionDep, skip: int = 0, limit: int = 10):
    return db.query(Person).offset(skip).limit(limit).all()
