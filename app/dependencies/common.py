import uuid
from http import HTTPStatus
from typing import Annotated, NotRequired, TypedDict

import sqlalchemy as sa
from fastapi import Depends, Query
from fastapi.dependencies.models import Dependant
from pydantic import BaseModel, model_validator
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute, Session
from starlette.requests import Request

from app.db.types import DerivationType
from app.errors import ApiError, ApiErrorCode
from app.filters.base import CustomFilter
from app.filters.brain_region import WithinBrainRegionDirection, filter_by_region
from app.queries.filter import filter_from_db
from app.queries.types import ApplyOperations
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
    filter_model: CustomFilter,
    filter_joins: dict[str, ApplyOperations] | None = None,
) -> Facets:
    facets = {}
    groupby_keys = ["id", "label", "type"]
    orderby_keys = ["label"]
    for facet_type, fields in name_to_facet_query_params.items():
        groupby_fields = {"type": sa.literal(facet_type), **fields}
        groupby_columns = [groupby_fields[key].label(key) for key in groupby_keys]  # type: ignore[attr-defined]
        groupby_ids = [sa.literal(i + 1) for i in range(len(groupby_columns))]
        facet_q = (
            # ensure that only the required joins are added
            filter_from_db(query, filter_model, filter_joins, forced_joins={facet_type})
            if filter_joins
            else query
        )
        # ensure that only the required columns are selected
        facet_q = (
            facet_q.with_only_columns(
                *groupby_columns,
                sa.func.count(sa.func.distinct(count_distinct_field)).label("count"),
            )
            .group_by(*groupby_ids)
            .order_by(*orderby_keys)
        )

        # use only the inner name as the key, in case of nested filters
        facets[facet_type.rsplit(".", maxsplit=1)[-1]] = [
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
        filter_model: CustomFilter,
        filter_joins: dict[str, ApplyOperations] | None = None,
    ):
        if not self.with_facets:
            return None

        return _get_facets(
            db,
            query,
            name_to_facet_query_params,
            count_distinct_field,
            filter_model=filter_model,
            filter_joins=filter_joins,
        )


class Search[T: DeclarativeBase](BaseModel):
    search: str | None = None

    def __call__(self, q: sa.Select[tuple[T]], vector_col: InstrumentedAttribute):
        if not self.search:
            return q

        return q.where(vector_col.match(self.search))


class InBrainRegionQuery(BaseModel):
    """Handle parameters for within_brain_region_* query params.

    Only `within_brain_region_direction` and `within_brain_region_brain_region_id` are required.
    `within_brain_region_hierarchy_id` exists for historical reasons, and is
    not used or verified: see https://github.com/openbraininstitute/entitycore/issues/567
    It will be deprecated.
    """

    within_brain_region_brain_region_id: uuid.UUID | None = None
    within_brain_region_direction: WithinBrainRegionDirection | None = None

    # only for backwards compat; ignored
    within_brain_region_hierarchy_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def check_range(self):
        if (
            self.within_brain_region_brain_region_id is not None
            and self.within_brain_region_direction is None
        ):
            raise ApiError(
                message=(
                    "Need to specify `within_brain_region_brain_region_id` "
                    "when `within_brain_region_direction` is specified"
                ),
                error_code=ApiErrorCode.INVALID_REQUEST,
                http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                details={
                    "within_brain_region_direction": f"{self.within_brain_region_direction}",
                },
            )

        if (
            self.within_brain_region_brain_region_id is None
            and self.within_brain_region_direction is not None
        ):
            raise ApiError(
                message=(
                    "Need to specify `within_brain_region_direction` "
                    "when `within_brain_region_brain_region_id` is specified"
                ),
                error_code=ApiErrorCode.INVALID_REQUEST,
                http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                details={
                    "within_brain_region_direction": f"{self.within_brain_region_direction}",
                },
            )
        return self

    def __call__(self, query: sa.Select, db_model_class):
        if (
            self.within_brain_region_brain_region_id is None
            and self.within_brain_region_direction is None
        ):
            return query

        # this was already checked by model_validator; adding asserts so typing is happy
        assert self.within_brain_region_brain_region_id  # noqa: S101
        assert self.within_brain_region_direction  # noqa: S101

        return filter_by_region(
            query=query,
            model=db_model_class,
            brain_region_id=self.within_brain_region_brain_region_id,
            direction=self.within_brain_region_direction,
        )


class DerivationQuery(BaseModel):
    used_id: uuid.UUID
    generated_id: uuid.UUID
    derivation_type: DerivationType


PaginationQuery = Annotated[PaginationRequest, Depends(PaginationRequest)]
FacetsDep = Annotated[WithFacets, Depends()]
SearchDep = Annotated[Search, Depends()]
InBrainRegionDep = Annotated[InBrainRegionQuery, Depends()]
DerivationQueryDep = Annotated[DerivationQuery, Depends()]
