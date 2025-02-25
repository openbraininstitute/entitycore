"""Entity repository module."""

from uuid import UUID

import sqlalchemy as sa

from app.db.auth import constrain_entity_query_to_project, constrain_to_accessible_entities
from app.db.model import Entity
from app.db.types import EntityType
from app.repository.base import BaseRepository


class EntityRepository(BaseRepository):
    """EntityRepository."""

    def get_readable_entity(
        self,
        entity_type: EntityType,
        entity_id: int,
        project_id: UUID,
    ) -> Entity:
        """Return a specific entity by type and id, readable by the given project.

        Args:
            entity_type: type of entity.
            entity_id: id of the entity.
            project_id: optional project id owning the entity.

        Returns:
            the selected entity if it's public or owned by project_id,
            or raises NoResultFound if the entity doesn't exist, or it's forbidden.
        """
        query = sa.select(Entity).where(Entity.id == entity_id, Entity.type == entity_type)
        query = constrain_to_accessible_entities(query, project_id=project_id)
        return self.db.execute(query).scalar_one()

    def get_writable_entity(
        self,
        entity_type: EntityType,
        entity_id: int,
        project_id: UUID,
        *,
        for_update: bool = False,
    ) -> Entity:
        """Return a specific entity by type and id, writable by the given project.

        Args:
            entity_type: type of entity.
            entity_id: id of the entity.
            project_id: project id owning the entity.
            for_update: if True, lock the row for update.

        Returns:
            the selected entity,
            or raises NoResultFound if the entity doesn't exist, or it's forbidden.
        """
        query = sa.select(Entity).where(Entity.id == entity_id, Entity.type == entity_type)
        query = constrain_entity_query_to_project(query, project_id=project_id)
        if for_update:
            query = query.with_for_update()
        return self.db.execute(query).scalar_one()
