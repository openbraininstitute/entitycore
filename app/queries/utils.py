import uuid
from itertools import chain
from typing import Literal, cast

import sqlalchemy as sa
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.db.auth import select_unauthorized_entities
from app.db.model import Identifiable, Person
from app.queries.types import NestedRelationships
from app.schemas.auth import UserContext, UserProfile
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


def is_user_authorized_for_deletion(  # noqa: PLR0911
    db: Session, user_context: UserContext, obj: Identifiable
) -> bool:
    if settings.APP_DISABLE_AUTH:
        return True

    # if there is no authorized_project_id it is a global resource
    if not (project_id := getattr(obj, "authorized_project_id", None)):
        return False

    # Service maintainers may delete public/private entities within their projects.
    if user_context.is_service_maintainer:
        return project_id in user_context.user_project_ids

    # from here and below public entities cannot be deleted
    if obj.authorized_public:  # pyright: ignore [reportAttributeAccessIssue]
        return False

    # Project admins may delete private entities within their projects
    if project_id in user_context.admin_project_ids:
        return True

    # Project members may delete only the private entities they themselves created
    if project_id in user_context.member_project_ids and (
        db_user := get_user(db, user_context.profile.subject)
    ):
        return db_user.created_by_id == obj.created_by_id

    return False


def create_associations_to_entities(
    db: Session,
    *,
    parent: Identifiable,
    json_model: BaseModel,
    nested_relationships: NestedRelationships,
    project_id: uuid.UUID | None,
    action: Literal["create", "update"],
) -> None:
    """Create association records between the left Identifiable and each of the right_id passed.

    Args:
        db: Database session.
        parent: Identifiable that is parent of the associations.
        json_model: Pydantic model of the left resourece.
        nested_relationships: Mapping of relationship keys to relationship dicts.
        project_id: Optional project ID for authorization checks.
        action: create or update the relationships.

    Raises:
        HTTPException: If any of the associated entities are not public or not in the same project,
            or if trying to update associations when it's not allowed.
    """
    # map relationship keys to lists of entity IDs to associate
    nested_relationship_ids: dict[str, list[uuid.UUID]] = cast(
        "dict[str, list[uuid.UUID]]",
        {
            relationship_key: relationship["nested_id_getter"](items=items)  # type: ignore[misc]
            for relationship_key, relationship in nested_relationships.items()
            if (items := getattr(json_model, relationship_key, None)) is not None
        },
    )

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
        if not (children := nested_relationship_ids.get(relationship_key)):
            continue
        if action == "update" and getattr(parent, relationship["relationship_name"]):
            raise HTTPException(
                status_code=409,
                detail=f"It is forbidden to update {relationship_key} if they exist.",
            )
        factory = relationship["db_model_factory"]
        for child_id in children:
            db_instance = factory(parent_id=parent.id, child_id=child_id)
            db.add(db_instance)

    db.flush()
