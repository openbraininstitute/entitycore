import uuid
from collections.abc import Callable
from typing import Annotated, NotRequired, TypedDict

import sqlalchemy as sa
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute, Session
from sqlalchemy.sql.base import ExecutableOption

from app.db.auth import constrain_to_accessible_entities
from app.db.model import Entity
from app.dependencies.common import PaginationQuery
from app.errors import ensure_result
from app.filters.base import CustomFilter
from app.schemas.auth import UserContext
from app.schemas.types import Facet, Facets, ListResponse, PaginationResponse


class FacetQueryParams(TypedDict):
    id: InstrumentedAttribute[uuid.UUID] | InstrumentedAttribute[int]
    label: InstrumentedAttribute[str]
    type: NotRequired[InstrumentedAttribute[str]]


def _get_facets(
    db: Session,
    query: sa.Select,
    name_to_facet_query_params: dict[str, FacetQueryParams],
    count_distinct_field: InstrumentedAttribute,
) -> Facets:
    facets = {}
    groupby_keys = ["id", "label", "type"]
    orderby_keys = ["label"]
    for facet_type, fields in name_to_facet_query_params.items():
        groupby_fields = {"type": sa.literal(facet_type), **fields}
        groupby_columns = [groupby_fields[key].label(key) for key in groupby_keys]  # type: ignore[attr-defined]
        groupby_ids = [sa.literal(i + 1) for i in range(len(groupby_columns))]
        facet_q = (
            query.with_only_columns(
                *groupby_columns,
                sa.func.count(sa.func.distinct(count_distinct_field)).label("count"),
            )
            .group_by(*groupby_ids)
            .order_by(*orderby_keys)
        )
        facets[facet_type] = [
            Facet.model_validate(row, from_attributes=True)
            for row in db.execute(facet_q).all()
            if row.id is not None  # exclude null rows if present
        ]

    return facets


class _FacetsDep(BaseModel):
    with_facets: bool = False

    def __call__(
        self,
        db: Session,
        query: sa.Select,
        name_to_facet_query_params: dict[str, FacetQueryParams],
        count_distinct_field: InstrumentedAttribute,
    ):
        if not self.with_facets:
            return None

        return _get_facets(db, query, name_to_facet_query_params, count_distinct_field)


class Search(BaseModel):
    search: str | None = None

    def __call__(self, q: sa.Select, vector_col: InstrumentedAttribute):
        if not self.search:
            return q

        return q.where(vector_col.match(self.search))


FacetsDep = Annotated[_FacetsDep, Depends()]
SearchDep = Annotated[Search, Depends()]


def router_read_one(
    *,
    id_: uuid.UUID,
    db: Session,
    db_model_class: type[Entity],
    authorized_project_id: uuid.UUID | None,
    response_schema_class: type[BaseModel],
    operations: list[ExecutableOption],
):
    with ensure_result(error_message=f"{db_model_class.__name__} not found"):
        query = constrain_to_accessible_entities(
            sa.select(db_model_class),
            authorized_project_id,
        ).filter(db_model_class.id == id_)
        for operation in operations:
            query = query.options(operation)

        row = db.execute(query).unique().scalar_one()

    return response_schema_class.model_validate(row)


def router_create_one(
    *,
    db: Session,
    db_model_class: type[Entity],
    json_model: BaseModel,
    authorized_project_id: uuid.UUID | None,
    response_schema_class: type[BaseModel],
):
    data = json_model.model_dump() | {"authorized_project_id": authorized_project_id}
    row = db_model_class(**data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return response_schema_class.model_validate(row)


def router_read_many(
    *,
    db: Session,
    db_model_class,
    user_context: UserContext,
    with_search: SearchDep,
    facets: FacetsDep,
    aliases: dict[type[DeclarativeBase], type[DeclarativeBase]],
    apply_filter_query_operations: Callable,
    apply_data_query_operations: Callable,
    pagination_request: PaginationQuery,
    response_schema_class: type[ListResponse],
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
    filter_query = with_search(
        filter_query,
        db_model_class.description_vector,
    )
    distinct_ids_subquery = (
        filter_model.sort(filter_query)
        .with_only_columns(db_model_class)
        .distinct()
        .offset(pagination_request.offset)
        .limit(pagination_request.page_size)
    ).subquery("distinct_ids")

    data_query = filter_model.sort(sa.Select(db_model_class)).join(
        distinct_ids_subquery, db_model_class.id == distinct_ids_subquery.c.id
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
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=facets(db, filter_query, name_to_facet_query_params, db_model_class.id),
    )

    return response
