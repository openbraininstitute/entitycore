import uuid
from collections.abc import Callable
from typing import Any, Protocol, TypedDict

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

type ApplyOperations[T: DeclarativeBase] = Callable[[sa.Select[tuple[T]]], sa.Select[tuple[T]]]


class SupportsModelValidate[T: BaseModel](Protocol):
    @classmethod
    def model_validate(cls, obj: Any, *args, **kwargs) -> T: ...


class AssociationCallable(Protocol):
    """Callable that should accept left_id and right_id and return a valid db model instance."""

    def __call__(self, *, left_id: uuid.UUID, right_id: uuid.UUID) -> DeclarativeBase: ...


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
