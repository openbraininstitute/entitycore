import uuid

import sqlalchemy as sa

import app.queries.entity
from app.db.auth import constrain_to_accessible_entities
from app.db.model import Entity
from app.db.types import EntityType
from app.db.utils import (
    ENTITY_TYPE_TO_CLASS,
    EntityTypeWithBrainRegion,
)
from app.dependencies.auth import UserContextDep
from app.dependencies.common import InBrainRegionDep
from app.dependencies.db import SessionDep
from app.filters.brain_region import get_family_query
from app.repository.group import RepositoryGroup
from app.schemas.auth import UserContext, UserContextWithProjectId
from app.schemas.entity import EntityCountRead


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


def count_entities_by_type(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    entity_types: list[EntityTypeWithBrainRegion],
    in_brain_region: InBrainRegionDep,
) -> EntityCountRead:
    """Count entities by their types.

    Returns:
        Dictionary with entity type as key and count as value
    """
    results = {}

    should_filter_brain_region = (
        in_brain_region
        and in_brain_region.within_brain_region_hierarchy_id is not None
        and in_brain_region.within_brain_region_brain_region_id is not None
    )

    filter_conditions = []
    if should_filter_brain_region:
        brain_region_cte = get_family_query(
            hierarchy_id=in_brain_region.within_brain_region_hierarchy_id,  # type: ignore[reportGeneralTypeIssues]
            brain_region_id=in_brain_region.within_brain_region_brain_region_id,  # type: ignore[reportGeneralTypeIssues]
            with_ascendants=in_brain_region.within_brain_region_ascendants,
        )

        for et in entity_types:
            entity_class = ENTITY_TYPE_TO_CLASS[EntityType(et.value)]
            q = sa.select(
                sa.literal(et.value).label("type"),
                sa.func.count(entity_class.id).label("count"),
            )
            q = constrain_to_accessible_entities(
                q, project_id=user_context.project_id, db_model_class=entity_class
            )
            q = q.join(brain_region_cte, entity_class.brain_region_id == brain_region_cte.c.id)  # type: ignore[reportAttributeAccessIssue]

            filter_conditions.append(q)

        union_q = sa.union_all(*filter_conditions)
        rows = db.execute(union_q).all()
        data = {row.type: row.count for row in rows}
        results = EntityCountRead.model_validate(data)

    else:
        query = sa.select(
            Entity.type.label("type"), sa.func.count(Entity.id).label("count")
        ).select_from(Entity)
        query = constrain_to_accessible_entities(
            query, project_id=user_context.project_id, db_model_class=Entity
        )
        query = query.where(Entity.type.in_(entity_types))
        query = query.group_by(Entity.type)

        rows = db.execute(query).all()
        data = {row.type: row.count for row in rows}
        results = EntityCountRead.model_validate(data)

    return results
