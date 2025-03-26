import uuid

from app.db.model import Entity
from app.db.types import EntityType
from app.errors import ensure_result
from app.repository.group import RepositoryGroup
from app.schemas.auth import UserContext, UserContextWithProjectId


def get_readable_entity(
    repos: RepositoryGroup,
    user_context: UserContext,
    entity_type: EntityType,
    entity_id: uuid.UUID,
) -> Entity:
    with ensure_result(f"Entity {entity_id} not found or forbidden"):
        return repos.entity.get_readable_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            project_id=user_context.project_id,
        )


def get_writable_entity(
    repos: RepositoryGroup,
    user_context: UserContextWithProjectId,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    *,
    for_update: bool = False,
) -> Entity:
    with ensure_result(f"Entity {entity_id} not found or forbidden"):
        return repos.entity.get_writable_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            project_id=user_context.project_id,
            for_update=for_update,
        )
