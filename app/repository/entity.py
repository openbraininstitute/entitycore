"""Entity repository module."""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import Row, or_, true

from app.db.model import Base, Entity
from app.db.types import EntityType
from app.repository.base import BaseRepository


class EntityRepository(BaseRepository):
    """EntityRepository."""

    _descendants = frozenset(
        mapper.class_.__tablename__
        for mapper in Base.registry.mappers
        if issubclass(mapper.class_, Entity)
    )

    @classmethod
    def _get_table(cls, name):
        try:
            table = Base.metadata.tables[name]
        except KeyError:
            err = f"Table {name} not found"
            raise RuntimeError(err) from None
        if name not in cls._descendants:
            err = f"Table {name} is not a subclass of entity"
            raise TypeError(err)
        return table

    def get_entity(
        self,
        entity_type: EntityType,
        entity_id: int | None = None,
    ) -> Row | None:
        """Return a specific entity by type and id.

        Args:
            entity_type: type of entity.
            entity_id: id of the entity.

        Returns:
            the selected entity, or None if the id doesn't exist.
        """
        table = self._get_table(entity_type.name)
        query = sa.select(table).where(table.c.id == entity_id)
        return self.db.execute(query).one_or_none()

    def get_entities(
        self,
        entity_type: EntityType,
        proj_id: UUID | None = None,
    ) -> Sequence[Row]:
        """Return a sequence of entities.

        Args:
            entity_type: type of entity.
            proj_id: optional project id owning the entity, used to filter the results.
                If not specified, only the public entities are returned.

        Returns:
            a sequence of entities.
        """
        table = self._get_table(entity_type.name)
        query = sa.select(table).where(
            or_(
                table.c.authorized_public == true(),
                (table.c.authorized_project_id == proj_id) if proj_id else true(),
            )
        )
        return self.db.execute(query).scalars().all()
