"""Generic derivation service."""

import uuid

from sqlalchemy import and_
from sqlalchemy.orm import aliased

from app.db.model import Derivation, Entity
from app.dependencies.auth import UserContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.entity import BasicEntityFilterDep
from app.queries.common import router_read_many
from app.schemas.base import BasicEntityRead
from app.schemas.types import ListResponse
from app.utils.routers import EntityRoute, entity_route_to_type


def read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    entity_route: EntityRoute,
    entity_id: uuid.UUID,
    pagination_request: PaginationQuery,
    entity_filter: BasicEntityFilterDep,
) -> ListResponse[BasicEntityRead]:
    """Return a list of basic entities used to generate the specified entity."""
    db_model_class = Entity
    generated_alias = aliased(Entity, flat=True, name="generated_alias")
    entity_type = entity_route_to_type(entity_route)
    # always needed regardless of the filter, so they cannot go to filter_keys
    apply_filter_query_operations = (
        lambda q: q.join(Derivation, db_model_class.id == Derivation.used_id)
        .join(generated_alias, Derivation.generated_id == generated_alias.id)
        .where(and_(generated_alias.id == entity_id, generated_alias.type == entity_type))
    )
    name_to_facet_query_params = filter_joins = None
    return router_read_many(
        db=db,
        db_model_class=db_model_class,
        authorized_project_id=user_context.project_id,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases={},
        apply_filter_query_operations=apply_filter_query_operations,
        apply_data_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=BasicEntityRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=entity_filter,
        filter_joins=filter_joins,
    )
