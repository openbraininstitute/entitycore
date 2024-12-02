from fastapi import APIRouter
from schemas.agent import PersonRead, PersonCreate
from models.agent import Person
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from typing import List
from dependencies.db import get_db

router = APIRouter(
    prefix="/person",
    tags=["person"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/{person_id}",
    response_model=PersonRead,
)
async def read_person(person_id: int, db: Session = Depends(get_db)):
    person = db.query(Person).filter(Person.id == person_id).first()

    if person is None:
        raise HTTPException(status_code=404, detail="person not found")
    ret = PersonRead.model_validate(person)
    return ret


@router.post("/", response_model=PersonRead)
def create_person(person: PersonCreate, db: Session = Depends(get_db)):
    db_person = Person(
        first_name=person.first_name,
        last_name=person.last_name,
        legacy_id=person.legacy_id,
    )
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person


@router.get("/", response_model=List[PersonRead])
async def read_person(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(Person).offset(skip).limit(limit).all()
    return users
