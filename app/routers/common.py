import uuid
from collections.abc import Callable
from contextlib import _GeneratorContextManager, nullcontext  # noqa: PLC2701
from typing import cast

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.auth import constrain_to_accessible_entities
from app.db.model import DescriptionVectorMixin, Entity, Root
from app.dependencies.common import FacetQueryParams, PaginationQuery, Search, WithFacets
from app.errors import ensure_result
from app.filters.base import CustomFilter
from app.schemas.auth import UserContext
from app.schemas.types import ListResponse, PaginationResponse

ApplyOperations = Callable[[sa.Select], sa.Select]
Aliases = dict[type[Root], type[Root]]
ContextManager = _GeneratorContextManager[None, None, None]


def router_read_one[T: BaseModel](
    *,
    id_: uuid.UUID,
    db: Session,
    db_model_class: type[Entity],
    authorized_project_id: uuid.UUID | None,
    response_schema_class: type[T],
    apply_operations: ApplyOperations | None,
):
    with ensure_result(error_message=f"{db_model_class.__name__} not found"):
        query = constrain_to_accessible_entities(
            sa.select(db_model_class),
            authorized_project_id,
        ).filter(db_model_class.id == id_)

        if apply_operations:
            query = apply_operations(query)

        row = db.execute(query).unique().scalar_one()

    return response_schema_class.model_validate(row)


def router_create_one[T: BaseModel](
    *,
    db: Session,
    authorized_project_id: uuid.UUID,
    db_model_class: type[Entity],
    json_model: BaseModel,
    response_schema_class: type[T],
    apply_operations: ApplyOperations | None = None,
    context_manager: ContextManager | None = None,
):
    with context_manager or nullcontext():
        data = json_model.model_dump() | {"authorized_project_id": authorized_project_id}
        row = db_model_class(**data)
        db.add(row)
        db.commit()
        db.refresh(row)

        q = sa.select(db_model_class).filter(db_model_class.id == row.id)

        if apply_operations:
            q = apply_operations(q)

        row = db.execute(q).unique().scalar_one()

        return response_schema_class.model_validate(row)


def router_read_many[T: BaseModel](
    *,
    db: Session,
    db_model_class: type[Entity],
    user_context: UserContext,
    with_search: Search,
    facets: WithFacets,
    aliases: Aliases,
    apply_filter_query_operations: ApplyOperations,
    apply_data_query_operations: ApplyOperations,
    pagination_request: PaginationQuery,
    response_schema_class: type[ListResponse[T]],
    name_to_facet_query_params: dict[str, FacetQueryParams],
    filter_model: CustomFilter,
):
    filter_query = constrain_to_accessible_entities(
        sa.select(db_model_class),
        project_id=user_context.project_id,
    )
    filter_query = apply_filter_query_operations(filter_query)

    filter_query = filter_model.filter(
        filter_query,
        aliases=aliases,
    )

    if issubclass(db_model_class, DescriptionVectorMixin):
        filter_query = with_search(
            filter_query,
            db_model_class.description_vector,  # type:ignore[attr-defined]
        )

    data_query = (
        filter_model.sort(filter_query)
        .with_only_columns(db_model_class)
        .distinct()
        .offset(pagination_request.offset)
        .limit(pagination_request.page_size)
    )
    data_query = apply_data_query_operations(data_query)

    # unique is needed b/c it contains results that include joined eager loads against collections
    data = db.execute(data_query).scalars().unique()

    total_items = db.execute(
        filter_query.with_only_columns(
            sa.func.count(sa.func.distinct(db_model_class.id)).label("count")
        )
    ).scalar_one()

    response = response_schema_class(
        data=cast("list[T]", data),
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=facets(db, filter_query, name_to_facet_query_params, db_model_class.id),
    )

    return response
