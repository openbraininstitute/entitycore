import uuid
from collections.abc import Collection, Iterable
from http import HTTPStatus
from typing import Annotated, Any, Protocol

import sqlalchemy as sa
from fastapi import Depends, Query
from fastapi.dependencies.models import Dependant
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute, Session
from starlette.requests import Request

from app.db.model import Identifiable
from app.db.types import DerivationType
from app.errors import ApiError, ApiErrorCode
from app.filters.brain_region import WithinBrainRegionDirection, filter_by_region
from app.queries.expand import EXPAND_DESCRIPTION, ExpandPaths, SchemaSpec, expand_enum
from app.queries.types import FacetQueryParamsMap
from app.schemas.types import Facet, Facets, PaginationRequest


class BuildFacetQuery(Protocol):
    """Build a query with the joins needed by all the given facet keys."""

    def __call__(self, *, facet_keys: Iterable[str]) -> sa.Select: ...


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


def _get_facets_group(
    db: Session,
    build_facet_query: BuildFacetQuery,
    name_to_facet_query_params: FacetQueryParamsMap,
    count_distinct_field: sa.SQLColumnExpression,
) -> dict[str, list[Facet]]:
    """Return the facets of the given keys, computed with a single query using GROUPING SETS.

    The rows are filtered and joined only once, and then aggregated once for each facet key.
    The result is the same of running a separate query for each key, but it avoids scanning
    the same rows many times.
    """
    facet_types = list(name_to_facet_query_params)
    id_columns: list[sa.ColumnElement] = []
    label_columns: list[sa.ColumnElement] = []
    type_columns: list[sa.ColumnElement | None] = []
    grouping_sets: list[sa.Tuple] = []
    for i, fields in enumerate(name_to_facet_query_params.values()):
        id_column = fields["id"].label(f"id_{i}")
        label_column = fields["label"].label(f"label_{i}")
        # the type is the facet key, unless the facet defines its own type column
        type_column = fields["type"].label(f"type_{i}") if "type" in fields else None
        id_columns.append(id_column)
        label_columns.append(label_column)
        type_columns.append(type_column)
        group_columns = [id_column, label_column]
        if type_column is not None:
            group_columns.append(type_column)
        grouping_sets.append(sa.tuple_(*group_columns))

    facet_q = build_facet_query(facet_keys=facet_types).with_only_columns(
        # bit i is 0 if the row belongs to the grouping set i, and 1 otherwise
        sa.func.grouping(*id_columns).label("grouping"),
        *id_columns,
        *label_columns,
        *(c for c in type_columns if c is not None),
        sa.func.count(sa.func.distinct(count_distinct_field)).label("count"),
    )
    # The rows of each facet have NULL in the labels of the other facets, so ordering by all the
    # labels in turn orders the rows of each facet by its own label. The id makes it deterministic.
    order_columns = [c for pair in zip(label_columns, id_columns, strict=True) for c in pair]
    facet_q = facet_q.group_by(sa.func.grouping_sets(*grouping_sets)).order_by(*order_columns)

    facets_by_type: dict[str, list[Facet]] = {facet_type: [] for facet_type in facet_types}
    last_index = len(facet_types) - 1
    for row in db.execute(facet_q).mappings():
        # find the only bit set to 0 in the grouping value
        index = next(
            i for i in range(len(facet_types)) if not row["grouping"] >> (last_index - i) & 1
        )
        # exclude null rows if present
        if row[f"id_{index}"] is not None:
            type_column = type_columns[index]
            facets_by_type[facet_types[index]].append(
                Facet(
                    id=row[f"id_{index}"],
                    label=row[f"label_{index}"],
                    count=row["count"],
                    type=facet_types[index] if type_column is None else row[f"type_{index}"],
                )
            )
    return facets_by_type


def _get_facets(
    db: Session,
    build_facet_query: BuildFacetQuery,
    name_to_facet_query_params: FacetQueryParamsMap,
    count_distinct_field: sa.SQLColumnExpression,
    multi_valued_facet_keys: Collection[str],
) -> Facets:
    """Return the facets of all the keys, using as few queries as possible.

    The keys that join a one-to-many relationship multiply the rows of the query, so they cannot
    be computed together without multiplying the rows by each of them.
    Each of them is computed in a separate query, and the first one also includes all the other
    keys.
    """
    params = name_to_facet_query_params
    single_valued = {k: v for k, v in params.items() if k not in multi_valued_facet_keys}
    multi_valued = [k for k in params if k in multi_valued_facet_keys]
    groups = [single_valued] if single_valued else []
    if multi_valued:
        groups = [{**single_valued, multi_valued[0]: params[multi_valued[0]]}]
        groups.extend({key: params[key]} for key in multi_valued[1:])
    facets_by_type: dict[str, list[Facet]] = {}
    for group in groups:
        facets_by_type.update(_get_facets_group(db, build_facet_query, group, count_distinct_field))
    # use only the inner name as the key, in case of nested filters
    return {
        facet_type.rsplit(".", maxsplit=1)[-1]: facets_by_type[facet_type]
        for facet_type in name_to_facet_query_params
    }


class WithFacets(BaseModel):
    with_facets: bool = False

    def __call__(
        self,
        db: Session,
        build_facet_query: BuildFacetQuery,
        name_to_facet_query_params: FacetQueryParamsMap,
        count_distinct_field: sa.SQLColumnExpression,
        multi_valued_facet_keys: Collection[str],
    ):
        if not self.with_facets:
            return None

        return _get_facets(
            db,
            build_facet_query,
            name_to_facet_query_params,
            count_distinct_field,
            multi_valued_facet_keys,
        )


class Search[T: DeclarativeBase](BaseModel):
    search: str | None = None

    def __call__(self, q: sa.Select[T], vector_col: InstrumentedAttribute):
        if not self.search:
            return q

        return q.where(vector_col.match(self.search))


class InBrainRegionQuery(BaseModel):
    """Handle parameters for within_brain_region_* query params.

    The parameters `within_brain_region_direction` and `within_brain_region_brain_region_id` can be
    both specified at the same time, or both left unspecified to not filter.

    The parameter `within_brain_region_hierarchy_id` is deprecated, and is
    not used or verified: see https://github.com/openbraininstitute/entitycore/issues/567
    It will be removed in a future version.
    """

    within_brain_region_brain_region_id: uuid.UUID | None = None
    within_brain_region_direction: WithinBrainRegionDirection | None = None

    # only for backwards compat; ignored
    # Not using Annotated syntax because apparently not showing the deprecated flag in openapi
    within_brain_region_hierarchy_id: uuid.UUID | None = Field(Query(None, deprecated=True))

    @model_validator(mode="after")
    def check_brain_region_id_and_direction(self):
        """Check within_brain_region_direction and within_brain_region_brain_region_id.

        They need to be both None, or both not None.
        """
        brain_region_id = self.within_brain_region_brain_region_id
        direction = self.within_brain_region_direction

        if brain_region_id is not None and direction is None:
            raise ApiError(
                message=(
                    "Need to specify `within_brain_region_direction` "
                    "when `within_brain_region_brain_region_id` is specified"
                ),
                error_code=ApiErrorCode.INVALID_REQUEST,
                http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                details={
                    "within_brain_region_brain_region_id": f"{brain_region_id}",
                    "within_brain_region_direction": f"{direction}",
                },
            )

        if brain_region_id is None and direction is not None:
            raise ApiError(
                message=(
                    "Need to specify `within_brain_region_brain_region_id` "
                    "when `within_brain_region_direction` is specified"
                ),
                error_code=ApiErrorCode.INVALID_REQUEST,
                http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                details={
                    "within_brain_region_brain_region_id": f"{brain_region_id}",
                    "within_brain_region_direction": f"{direction}",
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
        assert self.within_brain_region_brain_region_id  # ruff:ignore[assert]
        assert self.within_brain_region_direction  # ruff:ignore[assert]

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


def expand_query(schema: SchemaSpec, db_model_class: type[Identifiable]) -> Any:
    """Return the dependency of the `expand` query param, for endpoints returning schema.

    The allowed values are an enum named after the schema, documented in OpenAPI; invalid values
    return 422.

    Example:
        >>> ExpandDep = Annotated[ExpandPaths, expand_query(CircuitRead, Circuit)]
        >>> def read_one(..., expand: ExpandDep = frozenset()) -> CircuitRead: ...
    """
    expand_values = expand_enum(schema, db_model_class)

    def parse_expand(
        expand: Annotated[
            set[expand_values] | None,  # pyright: ignore[reportInvalidTypeForm]
            Query(description=EXPAND_DESCRIPTION),
        ] = None,
    ) -> ExpandPaths:
        return frozenset(expand or ())

    return Depends(parse_expand)
