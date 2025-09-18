import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db.auth import constrain_entity_query_to_project, constrain_to_accessible_entities
from app.db.model import Entity
from app.errors import ensure_result
from app.schemas.auth import UserContext


def get_readable_entity[T: Entity](
    db: Session,
    db_model_class: type[T],
    entity_id: uuid.UUID,
    user_context: UserContext | None,
) -> T:
    """Return a specific entity by type and id, readable by the given project.

    Args:
        db: db session.
        db_model_class: Entity subclass.
        entity_id: id of the entity.
        user_context: optional user context

    Returns:
        the selected entity if it's public or owned by project_id,
        or raises NoResultFound if the entity doesn't exist, or it's forbidden.
    """
    query = sa.select(db_model_class).where(db_model_class.id == entity_id)
    query = constrain_to_accessible_entities(query, user_context=user_context)
    with ensure_result(f"Entity {db_model_class.__name__} {entity_id} not found or forbidden"):
        return db.execute(query).scalar_one()


def get_writable_entity[T: Entity](
    db: Session,
    db_model_class: type[T],
    entity_id: uuid.UUID,
    project_id: uuid.UUID,
    *,
    for_update: bool = False,
) -> T:
    """Return a specific entity by type and id, writable by the given project.

    Args:
        db: db session.
        db_model_class: Entity subclass.
        entity_id: id of the entity.
        project_id: project id owning the entity.
        for_update: if True, lock the row for update.

    Returns:
        the selected entity,
        or raises NoResultFound if the entity doesn't exist, or it's forbidden.
    """
    query = sa.select(db_model_class).where(db_model_class.id == entity_id)
    query = constrain_entity_query_to_project(query, project_id=project_id)
    if for_update:
        query = query.with_for_update()
    with ensure_result(f"Entity {db_model_class.__name__} {entity_id} not found or forbidden"):
        return db.execute(query).scalar_one()
