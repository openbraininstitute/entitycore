"""Expandable fields of the read schemas: returned only when requested with `expand`.

`ExpandableSchema` is in `app.schemas.base`, which uses this module. How the fields are loaded,
the allowed values and the loader options are defined in `app.queries.expand` and
`app.queries.expand_loaders`.
"""

import types
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Union, get_args, get_origin

import sqlalchemy as sa
from pydantic import MISSING, BaseModel

# names of the custom loaders, defined in `app.queries.expand_loaders.CUSTOM_LOADERS`, named after
# the field they were written for
type ExpandLoaderName = Literal[
    "generated_from_derivations",
    "used_by_derivations",
    "measurement_annotation",
]


@dataclass(frozen=True, slots=True, kw_only=True)
class Expandable:
    """Marks a read-schema field as returned only when requested with `expand`.

    The field must allow and default to `MISSING`, and the schema must inherit from
    `ExpandableSchema`. A field is returned when its ORM attribute is loaded: `apply_expand` in
    `app.queries.expand` loads the requested ones, with a loader strategy or, when `loader` is
    set, with the custom loader of that name in `app.queries.expand_loaders.CUSTOM_LOADERS`.

    Args:
        attr: ORM attribute name, when different from the field name.
        loader: name of the custom loader, for fields needing more than a loader strategy.

    Example:
        >>> class SomeRead(ExpandableSchema):
        ...     summary: Annotated[dict | None | MISSING, Expandable()] = MISSING
    """

    attr: str | None = None
    loader: ExpandLoaderName | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ExpandableField:
    """An expandable field of a schema class, as collected at class creation."""

    name: str
    attr: str
    loader: ExpandLoaderName | None = None


def _expandable_marker(metadata: Sequence[Any]) -> Expandable | None:
    """Return the `Expandable` marker in the metadata of a field, if any."""
    return next((m for m in metadata if isinstance(m, Expandable)), None)


def _union_args(annotation: Any) -> tuple[Any, ...]:
    # Pydantic removes `Annotated` from the field annotations, keeping the metadata apart
    if get_origin(annotation) in {Union, types.UnionType}:
        return get_args(annotation)
    return (annotation,)


def _check_expandable_field(cls: type, name: str, annotation: Any, default: Any) -> None:
    prefix = f"{cls.__name__}.{name}"
    args = _union_args(annotation)
    if default is not MISSING or MISSING not in args:
        msg = f"{prefix}: expandable fields must allow and default to MISSING"
        raise TypeError(msg)
    if type(None) in args and any(get_origin(arg) in {list, Sequence} for arg in args):
        msg = f"{prefix}: expandable list fields must not allow None"
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
        if marker := _expandable_marker(field.metadata):
            _check_expandable_field(cls, name, field.annotation, field.default)
            expandable_fields[name] = ExpandableField(
                name=name, attr=marker.attr or name, loader=marker.loader
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
