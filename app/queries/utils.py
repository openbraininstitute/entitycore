import uuid
from itertools import chain
from typing import Literal

import sqlalchemy as sa
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.auth import select_unauthorized_entities
from app.db.model import Identifiable, Person
from app.queries.types import NestedRelationships, UpdateRelationshipPolicy
from app.schemas.auth import UserProfile
from app.schemas.utils import NOT_SET
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


def create_associations_to_entities(
    db: Session,
    *,
    left: Identifiable,
    json_model: BaseModel,
    nested_relationships: NestedRelationships,
    project_id: uuid.UUID | None,
    action: Literal["create", "update"],
) -> None:
    """Create association records between the left Identifiable and each of the right_id passed.

    Args:
        db: Database session.
        left: Identifiable on the left side of the associations.
        json_model: Pydantic model of the left resourece.
        nested_relationships: Mapping of relationship keys to relationship dicts.
        project_id: Optional project ID for authorization checks.
        action: create or update the relationships.

    Raises:
        HTTPException: If any of the associated entities are not public or not in the same project,
            or if trying to update associations when it's not allowed.
    """
    # map relationship keys to lists of entity IDs to associate, ignoring NOT_SET values
    nested_relationship_ids = {
        relationship_key: ids
        for relationship_key in nested_relationships
        if (ids := getattr(json_model, relationship_key)) != NOT_SET
    }

    associated_ids = list(chain.from_iterable(nested_relationship_ids.values()))

    # skip if all the nested_relationship_ids are empty
    if not associated_ids:
        return

    # the associated entities should be public, or in the same given project
    if (
        unaccessible_entities := db.execute(
            select_unauthorized_entities(associated_ids, project_id)
        )
        .scalars()
        .all()
    ):
        raise HTTPException(
            status_code=404,
            detail=f"Cannot access entities {', '.join(str(e) for e in unaccessible_entities)}",
        )

    for relationship_key, relationship in nested_relationships.items():
        # ignore empty ids
        if not (right_ids := nested_relationship_ids[relationship_key]):
            continue
        if action == "update":
            if relationship["update_policy"] == UpdateRelationshipPolicy.never:
                raise HTTPException(
                    status_code=409,
                    detail=f"It is forbidden to update {relationship_key} after the creation.",
                )
            if getattr(left, relationship["relationship_name"]):
                raise HTTPException(
                    status_code=409,
                    detail=f"It is forbidden to update {relationship_key} if they exist.",
                )
        factory = relationship["db_model_factory"]
        for right_id in right_ids:
            db_instance = factory(left_id=left.id, right_id=right_id)
            db.add(db_instance)

    db.flush()
