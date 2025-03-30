import uuid
from collections.abc import Callable
from contextlib import _GeneratorContextManager, contextmanager  # noqa: PLC2701
from typing import Annotated, NotRequired, TypedDict, cast

import sqlalchemy as sa
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import Select
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute, Session

from app.db.auth import constrain_to_accessible_entities
from app.db.model import Entity, Root
from app.dependencies.auth import UserContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
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


class Search[T: DeclarativeBase](BaseModel):
    search: str | None = None

    def __call__(self, q: sa.Select[tuple[T]], vector_col: InstrumentedAttribute):
        if not self.search:
            return q

        return q.where(vector_col.match(self.search))


FacetsDep = Annotated[_FacetsDep, Depends()]
SearchDep = Annotated[Search, Depends()]

type ApplyOperations[T: DeclarativeBase] = Callable[[Select[tuple[T]]], Select[tuple[T]]]
type Aliases[T: DeclarativeBase | Root] = dict[type[T], type[T]]
ContextManager = _GeneratorContextManager[None, None, None]


def router_read_one[T: BaseModel, M: DeclarativeBase](
    *,
    id_: uuid.UUID,
    db: Session,
    db_model_class: type[Entity],
    authorized_project_id: uuid.UUID | None,
    response_schema_class: type[T],
    apply_operations: ApplyOperations[M] | None,
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


ReadRouter = Callable[[UserContextDep, SessionDep, uuid.UUID], BaseModel]


def router_create_one(
    *,
    db: Session,
    user_context: UserContext,
    db_model_class: type[Entity],
    json_model: BaseModel,
    read_router: ReadRouter,
    context_manager: ContextManager | None,
):
    @contextmanager
    def dummy_context_manger():
        yield

    context_manager = context_manager or dummy_context_manger()

    with context_manager:
        data = json_model.model_dump() | {"authorized_project_id": user_context.project_id}
        row = db_model_class(**data)
        db.add(row)
        db.commit()
        db.refresh(row)
        return read_router(user_context, db, row.id)


def router_read_many[T: DeclarativeBase, M: BaseModel](
    *,
    db: Session,
    db_model_class,
    user_context: UserContext,
    with_search: Search[T],
    facets: _FacetsDep,
    aliases: Aliases,
    apply_filter_query_operations: ApplyOperations[T],
    apply_data_query_operations: ApplyOperations[T],
    pagination_request: PaginationQuery,
    response_schema_class: type[ListResponse[M]],
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

    data_query = (
        filter_query.with_only_columns(db_model_class)
        .distinct(db_model_class.id)
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
        data=cast("list[M]", data),
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=facets(db, filter_query, name_to_facet_query_params, db_model_class.id),
    )

    return response
