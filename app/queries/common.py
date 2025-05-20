import uuid
from collections.abc import Callable

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, Session

from app.db.auth import constrain_to_accessible_entities
from app.db.model import Entity, Identifiable
from app.dependencies.common import FacetQueryParams, PaginationQuery, Search, WithFacets
from app.errors import ensure_authorized_references, ensure_result, ensure_uniqueness
from app.filters.base import Aliases, CustomFilter
from app.schemas.types import ListResponse, PaginationResponse

from typing import TypeVar, Type
from app.logger import L

type ApplyOperations[T: DeclarativeBase] = Callable[[sa.Select[tuple[T]]], sa.Select[tuple[T]]]


def router_read_one[T: BaseModel, I: Identifiable](
    *,
    id_: uuid.UUID,
    db: Session,
    db_model_class: type[I],
    authorized_project_id: uuid.UUID | None,
    response_schema_class: type[T],
    apply_operations: ApplyOperations[I] | None,
) -> T:
    query = sa.select(db_model_class).where(db_model_class.id == id_)
    if issubclass(db_model_class, Entity):
        query = constrain_to_accessible_entities(query, authorized_project_id)
    if apply_operations:
        query = apply_operations(query)
    with ensure_result(error_message=f"{db_model_class.__name__} not found"):
        row = db.execute(query).unique().scalar_one()
    return response_schema_class.model_validate(row)


T = TypeVar("T", bound=BaseModel)
I = TypeVar("I")

from app.schemas.morphology import PipelineType  
def router_create_one[
    T: BaseModel, I: I
](
    *,
    db: Session,
    db_model_class: type[I],
    authorized_project_id: uuid.UUID | None,
    json_model: BaseModel,
    response_schema_class: type[T],
    apply_operations: ApplyOperations | None = None,
    extra_data: dict | None = None,
) -> I:  # Return SQLAlchemy model (I) instead of Pydantic model (T)
    data = json_model.model_dump()
    if issubclass(db_model_class, Entity):
        data |= {"authorized_project_id": authorized_project_id}
    if extra_data:
        valid_columns = {c.name for c in db_model_class.__table__.columns}
        extra_data_for_model = {k: v for k, v in extra_data.items() if k in valid_columns}
        data |= extra_data_for_model
    L.info("Data passed to %s: %s", db_model_class.__name__, data)
    row = db_model_class(**data)
    
    db.add(row)
    if apply_operations:
        for operation in apply_operations:
            operation(db, row)
    
    L.info("Created row: %s", row.__dict__)
    return row  # Return the SQLAlchemy object


def router_read_many[T: BaseModel, I: Identifiable](
    *,
    db: Session,
    db_model_class: type[I],
    authorized_project_id: uuid.UUID | None,
    with_search: Search[I] | None,
    facets: WithFacets | None,
    aliases: Aliases | None,
    apply_filter_query_operations: ApplyOperations[I] | None,
    apply_data_query_operations: ApplyOperations[I] | None,
    pagination_request: PaginationQuery,
    response_schema_class: type[T],
    response_schema_transformer: Callable[[I], T] | None = None, 
    name_to_facet_query_params: dict[str, FacetQueryParams] | None,
    filter_model: CustomFilter,
) -> ListResponse[T]:
    filter_query = sa.select(db_model_class)
    if issubclass(db_model_class, Entity):
        filter_query = constrain_to_accessible_entities(
            filter_query, project_id=authorized_project_id
        )

    if apply_filter_query_operations:
        filter_query = apply_filter_query_operations(filter_query)

    filter_query = filter_model.filter(
        filter_query,
        aliases=aliases,
    )

    if with_search and (description_vector := getattr(db_model_class, "description_vector", None)):
        filter_query = with_search(filter_query, description_vector)

    data_query = (
        filter_model.sort(filter_query)
        .with_only_columns(db_model_class)
        .distinct()
        .offset(pagination_request.offset)
        .limit(pagination_request.page_size)
    )

    if apply_data_query_operations:
        data_query = apply_data_query_operations(data_query)

    # unique is needed b/c it contains results that include joined eager loads against collections
    data = db.execute(data_query).scalars().unique()

    total_items = db.execute(
        filter_query.with_only_columns(
            sa.func.count(sa.func.distinct(db_model_class.id)).label("count")
        )
    ).scalar_one()

    return ListResponse[response_schema_class](
        data=[response_schema_class.model_validate(row) for row in data],
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=facets(db, filter_query, name_to_facet_query_params, db_model_class.id)
        if facets and name_to_facet_query_params
        else None,
    )
