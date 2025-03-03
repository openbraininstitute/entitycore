from app.db.model import Entity
from app.db.types import EntityWithAssets
from app.errors import ensure_result
from app.repository.group import RepositoryGroup
from app.schemas.base import ProjectContext


def get_readable_entity(
    repos: RepositoryGroup,
    project_context: ProjectContext,
    entity_type: EntityWithAssets,
    entity_id: int,
) -> Entity:
    with ensure_result(f"Entity {entity_id} not found or forbidden"):
        return repos.entity.get_readable_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            project_id=project_context.project_id,
        )


def get_writable_entity(
    repos: RepositoryGroup,
    project_context: ProjectContext,
    entity_type: EntityWithAssets,
    entity_id: int,
    *,
    for_update: bool = False,
) -> Entity:
    with ensure_result(f"Entity {entity_id} not found or forbidden"):
        return repos.entity.get_writable_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            project_id=project_context.project_id,
            for_update=for_update,
        )
