import uuid
from collections.abc import Callable

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, Session

from app.db.auth import constrain_entity_query_to_project, constrain_to_accessible_entities
from app.db.model import Entity, Identifiable
from app.db.utils import load_db_model_from_pydantic
from app.dependencies.common import FacetQueryParams, PaginationQuery, Search, WithFacets
from app.errors import (
    ensure_authorized_references,
    ensure_foreign_keys_integrity,
    ensure_result,
    ensure_uniqueness,
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
    """Read a model from the database.

    Args:
        id_: id of the entity to read.
        db: database session.
        db_model_class: database model class.
        authorized_project_id: id of the authorized project.
        response_schema_class: Pydantic schema class for the returned data.
        apply_operations: transformer function that modifies the select query.

    Returns:
        the model data as a Pydantic model.
    """
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
    """Create a model in the database.

    Args:
        db: database session.
        db_model_class: database model class.
        authorized_project_id: id of the authorized project.
        json_model: instance of the Pydantic model.
        response_schema_class: Pydantic schema class for the returned data.
        apply_operations: transformer function that modifies the select query.

    Returns:
        the written model data as a Pydantic model.
    """
    db_model_instance = load_db_model_from_pydantic(
        json_model, db_model_class, authorized_project_id=authorized_project_id
    )
    with (
        ensure_uniqueness(f"{db_model_class.__name__} already exists or breaks unique constraints"),
        ensure_authorized_references(
            f"One of the entities referenced by {db_model_class.__name__} "
            f"is not public or not owned by the user"
        ),
    ):
        db.add(db_model_instance)
        db.flush()
    if apply_operations:
        q = sa.select(db_model_class).where(db_model_class.id == db_model_instance.id)
        q = apply_operations(q)
        db_model_instance = db.execute(q).unique().scalar_one()
    else:
        db.refresh(db_model_instance)
    return response_schema_class.model_validate(db_model_instance)


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
    filter_model: CustomFilter,
) -> ListResponse[T]:
    """Read multiple models from the database.

    Args:
        db: database session.
        db_model_class: database model class.
        authorized_project_id: project id for filtering the resources.
        with_search: search query (str).
        facets: facet query (bool).
        aliases: dict of table aliases for the filter query.
        apply_filter_query_operations: optional callable to transform the filter query.
        apply_data_query_operations: optional callable to transform the data query.
        pagination_request: pagination.
        response_schema_class: Pydantic schema class for the returned data.
        name_to_facet_query_params: dict of FacetQueryParams for building the facets.
        filter_model: instance of CustomFilter for filtering and sorting data.

    Returns:
        the list of model data, pagination, and facets as a Pydantic model.
    """
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


def router_delete_one[T: BaseModel, I: Identifiable](
    *,
    id_: uuid.UUID,
    db: Session,
    db_model_class: type[I],
    authorized_project_id: uuid.UUID | None,
) -> None:
    """Delete a model from the database.

    Args:
        id_: id of the entity to read.
        db: database session.
        db_model_class: database model class.
        authorized_project_id: project id for filtering the resources.
    """
    query = sa.delete(db_model_class).where(db_model_class.id == id_)
    if issubclass(db_model_class, Entity) and authorized_project_id:
        query = constrain_entity_query_to_project(query, authorized_project_id)
    query = query.returning(db_model_class.id)
    with (
        ensure_result(error_message=f"{db_model_class.__name__} not found"),
        ensure_foreign_keys_integrity(
            error_message=(
                f"{db_model_class.__name__} cannot be deleted "
                f"because of foreign keys integrity violation"
            )
        ),
    ):
        db.execute(query).one()
