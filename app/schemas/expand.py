"""Expandable fields of the read schemas: returned only when requested with `expand`.

The paths, the allowed values and the loader options are built in `app.queries.expand`.
"""

import types
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import cache
from typing import Annotated, Any, ClassVar, Protocol, Union, get_args, get_origin

import sqlalchemy as sa
from pydantic import MISSING, model_validator
from sqlalchemy import orm

from app.schemas.base import Schema


class ExpandLoader(Protocol):
    """Builds the loader options of an expandable field (see `Expandable`)."""

    def __call__(
        self,
        parent: orm.Load | None,
        attr: orm.QueryableAttribute,
        qualifiers: frozenset[str] | None,
        /,
    ) -> Sequence[orm.Load]:
        """Return the loader options of the field.

        Args:
            parent: load of the parent object, or None at the root of the query.
            attr: ORM attribute of the field.
            qualifiers: requested qualifiers, or None when requested without qualifier.

        Example:
            >>> def load(parent, attr, qualifiers):
            ...     return [expand_load(parent, "selectinload", attr)]
        """
        ...


@dataclass(frozen=True, slots=True, kw_only=True)
class Expandable:
    """Marks a read-schema field as returned only when requested with `expand`.

    The field must default to `MISSING`, and the schema must inherit from `ExpandableSchema`.
    A field is returned when its ORM attribute is loaded: `apply_expand` in `app.queries.expand`
    loads the requested ones.

    Args:
        attr: ORM attribute name, when different from the field name.
        loader: builder of the loader options, for relationships needing more than a
            `selectinload` (e.g. nested relationships of the related object, or qualifiers).
        qualifiers: values accepted after `:` (e.g. the derivation types); they require a loader.

    Example:
        >>> class SomeRead(ExpandableSchema):
        ...     summary: Annotated[dict | None | MISSING, Expandable()] = MISSING
    """

    attr: str | None = None
    loader: ExpandLoader | None = None
    qualifiers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class ExpandableField:
    """An expandable field of a schema class, as collected at class creation."""

    name: str
    attr: str
    marker: Expandable


def expand_load(parent: orm.Load | None, strategy: str, attr: Any) -> orm.Load:
    """Return the loader option `strategy` (e.g. `selectinload`) for attr, chained to parent.

    Example:
        >>> expand_load(None, "selectinload", Entity.assets)  # selectinload(Entity.assets)
    """
    if parent is None:
        return getattr(orm, strategy)(attr)
    return getattr(parent, strategy)(attr)


def expandable_marker(metadata: Sequence[Any]) -> Expandable | None:
    """Return the `Expandable` marker in the metadata of a field, if any."""
    return next((m for m in metadata if isinstance(m, Expandable)), None)


def _union_args(annotation: Any) -> tuple[Any, ...]:
    while get_origin(annotation) is Annotated:
        annotation = get_args(annotation)[0]
    if get_origin(annotation) in {Union, types.UnionType}:
        return get_args(annotation)
    return (annotation,)


def _check_expandable_field(
    cls: type, name: str, annotation: Any, marker: Expandable, default: Any
) -> None:
    prefix = f"{cls.__name__}.{name}"
    if default is not MISSING:
        msg = f"{prefix}: expandable fields must default to MISSING"
        raise TypeError(msg)
    args = _union_args(annotation)
    if type(None) in args and any(get_origin(arg) in {list, Sequence} for arg in args):
        msg = f"{prefix}: expandable list fields must not allow None"
        raise TypeError(msg)
    if marker.qualifiers and marker.loader is None:
        msg = f"{prefix}: qualifiers require a loader"
        raise TypeError(msg)


class _HideUnloaded:
    """Read-only view of an ORM instance used to validate an `ExpandableSchema`.

    It raises AttributeError for the expandable fields whose ORM attribute is not loaded, so that
    Pydantic uses their MISSING default without accessing (and lazy loading) the attribute, and
    maps the expandable field names to their ORM attribute names.
    """

    __slots__ = ("_hidden", "_instance", "_renamed")

    def __init__(self, instance: Any, hidden: frozenset[str], renamed: dict[str, str]) -> None:
        self._instance = instance
        self._hidden = hidden
        self._renamed = renamed

    def __getattr__(self, name: str) -> Any:
        if name in self._hidden:
            raise AttributeError(name)
        return getattr(self._instance, self._renamed.get(name, name))


class ExpandableSchema(Schema):
    """Base class of the schemas with expandable fields (see `Expandable`).

    When validated from an ORM instance, an expandable field is set only if its attribute is
    loaded, and it is omitted from the output otherwise. An attribute can also be loaded without
    being requested, e.g. if the instance was already loaded in the same session.
    """

    # field name -> expandable field, collected at class creation
    __expandable_fields__: ClassVar[dict[str, ExpandableField]] = {}

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:  # ruff:ignore[bad-dunder-method-name]
        """Collect and check the expandable fields of the class."""
        super().__pydantic_init_subclass__(**kwargs)
        expandable_fields = {}
        for name, field in cls.model_fields.items():
            if marker := expandable_marker(field.metadata):
                _check_expandable_field(cls, name, field.annotation, marker, field.default)
                expandable_fields[name] = ExpandableField(
                    name=name, attr=marker.attr or name, marker=marker
                )
        cls.__expandable_fields__ = expandable_fields

    @model_validator(mode="wrap")
    @classmethod
    def _skip_unloaded_expandable_fields(cls, data: Any, handler: Callable[[Any], Any]) -> Any:
        expandable_fields = cls.__expandable_fields__
        if not expandable_fields or (state := sa.inspect(data, raiseerr=False)) is None:
            return handler(data)
        unloaded = state.unloaded
        hidden = frozenset(f.name for f in expandable_fields.values() if f.attr in unloaded)
        renamed = {f.name: f.attr for f in expandable_fields.values() if f.name != f.attr}
        return handler(_HideUnloaded(data, hidden, renamed))


@cache
def expandable_fields(schema_class: type[Schema]) -> dict[str, ExpandableField]:
    """Return the expandable fields of a schema class.

    Raises:
        TypeError: if the class has expandable fields but doesn't inherit from ExpandableSchema.
    """
    if issubclass(schema_class, ExpandableSchema):
        return schema_class.__expandable_fields__
    if any(expandable_marker(f.metadata) for f in schema_class.model_fields.values()):
        msg = (
            f"{schema_class.__name__} has expandable fields and must inherit from ExpandableSchema"
        )
        raise TypeError(msg)
    return {}
