import uuid
from collections.abc import Callable

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, Session

from app.db.auth import constrain_to_accessible_entities
from app.db.model import Entity, Identifiable
from app.dependencies.common import FacetQueryParams, PaginationQuery, Search, WithFacets
from app.errors import (
    ensure_authorized_references,
    ensure_result,
    ensure_uniqueness,
    ensure_valid_foreign_keys,
)
from app.filters.base import Aliases, CustomFilter
from app.schemas.types import ListResponse, PaginationResponse

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


def router_create_one[T: BaseModel, I: Identifiable](
    *,
    db: Session,
    db_model_class: type[I],
    authorized_project_id: uuid.UUID | None,
    json_model: BaseModel,
    response_schema_class: type[T],
    apply_operations: ApplyOperations | None = None,
) -> T:
    data = json_model.model_dump(by_alias=True)
    if issubclass(db_model_class, Entity):
        data |= {"authorized_project_id": authorized_project_id}
    row = db_model_class(**data)
    with (
        ensure_valid_foreign_keys("One or more foreign keys do not exist in the db"),
        ensure_uniqueness(error_message=f"{db_model_class.__name__} already exists"),
        ensure_authorized_references(
            f"One of the entities referenced by {db_model_class.__name__} "
            f"is not public or not owned by the user"
        ),
    ):
        db.add(row)
        db.flush()
        db.refresh(row)
    if apply_operations:
        q = sa.select(db_model_class).where(db_model_class.id == row.id)
        q = apply_operations(q)
        row = db.execute(q).unique().scalar_one()

    return response_schema_class.model_validate(row)


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
    name_to_facet_query_params: dict[str, FacetQueryParams] | None,
    filter_model: CustomFilter[I],
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
