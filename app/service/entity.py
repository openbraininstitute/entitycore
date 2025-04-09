import uuid

import app.queries.entity
from app.db.model import Base, Entity
from app.db.types import EntityType
from app.repository.group import RepositoryGroup
from app.schemas.auth import UserContext, UserContextWithProjectId

ENTITY_TYPE_TO_CLASS: dict[EntityType, type[Entity]] = {
    EntityType[mapper.class_.__tablename__]: mapper.class_
    for mapper in Base.registry.mappers
    if hasattr(EntityType, mapper.class_.__tablename__)
}


def get_readable_entity(
    repos: RepositoryGroup,
    *,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
) -> Entity:
    db_model_class = ENTITY_TYPE_TO_CLASS[entity_type]
    return app.queries.entity.get_readable_entity(
        db=repos.db,
        db_model_class=db_model_class,
        entity_id=entity_id,
        project_id=user_context.project_id,
    )


def get_writable_entity(
    repos: RepositoryGroup,
    *,
    user_context: UserContextWithProjectId,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    for_update: bool = False,
) -> Entity:
    db_model_class = ENTITY_TYPE_TO_CLASS[entity_type]
    return app.queries.entity.get_writable_entity(
        db=repos.db,
        db_model_class=db_model_class,
        entity_id=entity_id,
        project_id=user_context.project_id,
        for_update=for_update,
    )
