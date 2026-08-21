import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, NotRequired, Protocol, TypedDict

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

type ApplyOperations[T: DeclarativeBase] = Callable[[sa.Select[tuple[T]]], sa.Select[tuple[T]]]


type FacetQueryParamsMap = Mapping[str, FacetQueryParams]
type JoinSpecMap = Mapping[str, JoinSpec]


class FacetQueryParams(TypedDict):
    id: sa.SQLColumnExpression[uuid.UUID]
    label: sa.SQLColumnExpression[str]
    type: NotRequired[sa.SQLColumnExpression[str]]


@dataclass(frozen=True)
class JoinSpec:
    """Join specification for a single filter/facet key.

    Attributes:
        join: Join applied for sorting (outer join for nullable FKs, inner for non-null).
            Also used as fallback when filter_join/facet_join are not specified.
        filter_join: Inner join override used when a filter is actively set on a nullable FK.
            More selective than the outer join, safe because null-filtering is not supported.
            Defaults to join when not specified.
        facet_join: Join override used when computing facet labels. May include joins that
            are not needed for filtering or sorting but are required by the facet label
            expression. Defaults to join when not specified.
    """

    join: ApplyOperations
    filter_join: ApplyOperations | None = None
    facet_join: ApplyOperations | None = None

    def apply_join(self, q: sa.Select) -> sa.Select:
        return self.join(q)

    def apply_filter_join(self, q: sa.Select) -> sa.Select:
        return (self.filter_join or self.join)(q)

    def apply_facet_join(self, q: sa.Select) -> sa.Select:
        return (self.facet_join or self.join)(q)


class SupportsModelValidate[T: BaseModel](Protocol):
    @classmethod
    def model_validate(cls, obj: Any, *args, **kwargs) -> T: ...


class AssociationCallable(Protocol):
    """Callable that should accept parent_id and child_id and return a valid db model instance."""

    def __call__(self, *, parent_id: uuid.UUID, child_id: uuid.UUID) -> DeclarativeBase: ...


class NestedIdGetter(Protocol):
    """Callable that should return the list of ids from the json model."""

    def __call__(self, *, items: list) -> list[uuid.UUID]: ...


class NestedRelationship(TypedDict):
    """Nested relationship dict, used for creating relationships in entities and activities."""

    relationship_name: str  # name of the relationship in the db model
    db_model_factory: AssociationCallable  # callable that should return a new db model instance
    nested_id_getter: NestedIdGetter  # callable that should return the list of ids from json


# mapping relationship_key -> relationship, where:
# - relationship_key is the key in the Create schema of the resource
# - relationship is a dict of type NestedRelationship
NestedRelationships = dict[str, NestedRelationship]
