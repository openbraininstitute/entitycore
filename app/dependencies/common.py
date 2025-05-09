import uuid
from http import HTTPStatus
from typing import Annotated, NotRequired, TypedDict

import sqlalchemy as sa
from fastapi import Depends, Query
from fastapi.dependencies.models import Dependant
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute, Session
from starlette.requests import Request

from app.errors import ApiError, ApiErrorCode
from app.filters.brain_region import filter_by_hierarchy_and_region
from app.schemas.types import Facet, Facets, PaginationRequest


def forbid_extra_query_params(
    request: Request,
    *,
    allow_extra_params: Annotated[bool, Query(include_in_schema=False)] = False,
) -> None:
    """Forbid extra query parameters.

    If needed, this can be disabled per request by setting the param `allow_extra_params=true`,
    but this option is intended for internal use, and it might be removed in the future.
    """

    def traverse(dependant: Dependant, params: dict[str, bool]) -> dict[str, bool]:
        """Update params from the query_params of all the dependencies.

        Return a dict of all the known params and the boolean values of `include_in_schema`.
        """
        params.update(
            (param.alias, getattr(param.field_info, "include_in_schema", True))
            for param in dependant.query_params
        )
        for dependency in dependant.dependencies:
            traverse(dependency, params)
        return params

    if allow_extra_params:
        return

    # possible improvement: cache allowed_params by request.scope["method"], request.scope["path"]
    allowed_params = traverse(request.scope["route"].dependant, params={})
    query_params = set(request.query_params.keys())
    if unknown_params := query_params.difference(allowed_params):
        raise ApiError(
            message="Unknown query parameters",
            error_code=ApiErrorCode.INVALID_REQUEST,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            details={
                "unknown_params": sorted(unknown_params),
                "allowed_params": sorted(
                    param
                    for param, include_in_schema in allowed_params.items()
                    if include_in_schema
                ),
            },
        )


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


class WithFacets(BaseModel):
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


class InBrainRegionQuery(BaseModel):
    within_brain_region_hierachy_id: uuid.UUID | None = None
    within_brain_region_brain_region_id: uuid.UUID | None = None
    within_brain_region_ascendants: bool = False

    def __call__(self, query: sa.Select, db_model_class):
        if (
            self.within_brain_region_hierachy_id is None
            or self.within_brain_region_brain_region_id is None
        ):
            return query

        return filter_by_hierarchy_and_region(
            query=query,
            model=db_model_class,
            hierarchy_id=self.within_brain_region_hierachy_id,
            brain_region_id=self.within_brain_region_brain_region_id,
            with_ascendants=self.within_brain_region_ascendants,
        )


PaginationQuery = Annotated[PaginationRequest, Depends(PaginationRequest)]
FacetsDep = Annotated[WithFacets, Depends()]
SearchDep = Annotated[Search, Depends()]
InBrainRegionDep = Annotated[InBrainRegionQuery, Depends()]
