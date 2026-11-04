"""Expandable fields of the read schemas: returned only when requested with `expand`.

`ExpandableSchema` is in `app.schemas.base`, which uses this module; the paths, the allowed
values and the loader options are built in `app.queries.expand`.
"""

import types
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Annotated, Any, Protocol, Union, get_args, get_origin

import sqlalchemy as sa
from pydantic import MISSING, BaseModel
from sqlalchemy import orm


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


def collect_expandable_fields(cls: type[BaseModel]) -> dict[str, ExpandableField]:
    """Return the expandable fields of a schema class, after checking their declaration."""
    expandable_fields = {}
    for name, field in cls.model_fields.items():
        if marker := expandable_marker(field.metadata):
            _check_expandable_field(cls, name, field.annotation, marker, field.default)
            expandable_fields[name] = ExpandableField(
                name=name, attr=marker.attr or name, marker=marker
            )
    return expandable_fields


def validate_loaded(
    expandable_fields: dict[str, ExpandableField], data: Any, handler: Callable[[Any], Any]
) -> Any:
    """Validate data with handler, skipping the unloaded expandable fields of an ORM instance.

    Used by the wrap validator of `ExpandableSchema`; other inputs are validated as they are.
    """
    if not expandable_fields or (state := sa.inspect(data, raiseerr=False)) is None:
        return handler(data)
    unloaded = state.unloaded
    hidden = frozenset(f.name for f in expandable_fields.values() if f.attr in unloaded)
    renamed = {f.name: f.attr for f in expandable_fields.values() if f.name != f.attr}
    return handler(_HideUnloaded(data, hidden, renamed))
