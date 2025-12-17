import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db.model import Person
from app.schemas.auth import UserProfile
from app.utils.uuid import create_uuid


def get_or_create_user_agent(db: Session, user_profile: UserProfile) -> Person:
    if db_agent := get_user(db, user_profile.subject):
        return db_agent

    agent_id = create_uuid()

    db_agent = Person(
        id=agent_id,
        pref_label=user_profile.name,
        given_name=user_profile.given_name,
        family_name=user_profile.family_name,
        sub_id=user_profile.subject,
        created_by_id=agent_id,
        updated_by_id=agent_id,
    )

    db.add(db_agent)
    db.flush()

    return db_agent


def get_user(db: Session, subject_id: uuid.UUID) -> Person | None:
    query = sa.select(Person).where(Person.sub_id == subject_id)
    return db.execute(query).scalars().first()
