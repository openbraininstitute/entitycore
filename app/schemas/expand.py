"""Expandable fields of the read schemas: returned only when requested with `expand`.

`ExpandableSchema` is in `app.schemas.base`, which uses this module. How the fields are loaded,
the allowed values and the loader options are defined in `app.queries.expand` and
`app.queries.expand_loaders`.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Union, get_args, get_origin

import sqlalchemy as sa
from pydantic import MISSING, BaseModel
from pydantic.fields import FieldInfo

# custom loaders in `app.queries.expand_loaders.CUSTOM_LOADERS`, named after their field
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
    The ORM attribute has the name of the field, or its `validation_alias` if set.

    Args:
        loader: name of the custom loader, for fields needing more than a loader strategy.

    Example:
        >>> class SomeRead(ExpandableSchema):
        ...     summary: Annotated[dict | None | MISSING, Expandable()] = MISSING
    """

    loader: ExpandLoaderName | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ExpandableField:
    """An expandable field of a schema class, resolved from its `Expandable` marker and the field.

    Resolved at class creation, and keyed by the field name in `__expandable_fields__`.

    Attributes:
        attr: name of the ORM attribute of the field (see `orm_attr`).
        loader: name of the custom loader, if any.
    """

    attr: str
    loader: ExpandLoaderName | None = None


def orm_attr(name: str, field: FieldInfo) -> str:
    """Return the name of the ORM attribute read by the schema field `name`.

    Pydantic reads it from the ORM instance: the `validation_alias` if a string, or the name.

    Example:
        >>> orm_attr("species", StrainRead.model_fields["species"])
        'species'
    """
    alias = field.validation_alias
    return alias if isinstance(alias, str) else name


def _expandable_marker(metadata: Sequence[Any]) -> Expandable | None:
    """Return the `Expandable` marker in the metadata of a field, if any."""
    return next((m for m in metadata if isinstance(m, Expandable)), None)


def _union_args(annotation: Any) -> tuple[Any, ...]:
    # Pydantic removes `Annotated` from the field annotations, keeping the metadata apart
    if get_origin(annotation) is Union:
        return get_args(annotation)
    return (annotation,)


def _check_expandable_field(cls: type, name: str, field: FieldInfo) -> None:
    prefix = f"{cls.__name__}.{name}"
    args = _union_args(field.annotation)
    if field.default is not MISSING or MISSING not in args:
        msg = f"{prefix}: expandable fields must allow and default to MISSING"
        raise TypeError(msg)
    if type(None) in args and any(get_origin(arg) in {list, Sequence} for arg in args):
        msg = f"{prefix}: expandable list fields must not allow None"
        raise TypeError(msg)
    if not isinstance(field.validation_alias, str | None):
        # e.g. AliasPath: the attribute read can't be hidden when not loaded
        msg = f"{prefix}: the validation_alias of expandable fields must be a string"
        raise TypeError(msg)


class _HideUnloaded:
    """Read-only view of an ORM instance used to validate an `ExpandableSchema`.

    It raises AttributeError for the ORM attributes of the expandable fields that are not loaded,
    so that Pydantic uses their MISSING default without accessing (and lazy loading) them.
    """

    __slots__ = ("_hidden", "_instance")

    def __init__(self, instance: Any, hidden: frozenset[str]) -> None:
        self._instance = instance
        self._hidden = hidden

    def __getattr__(self, attr: str) -> Any:
        if attr in self._hidden:
            raise AttributeError(attr)
        return getattr(self._instance, attr)


def collect_expandable_fields(cls: type[BaseModel]) -> dict[str, ExpandableField]:
    """Return the expandable fields of a schema class by field name, after checking them."""
    expandable_fields = {}
    for name, field in cls.model_fields.items():
        if marker := _expandable_marker(field.metadata):
            _check_expandable_field(cls, name, field)
            expandable_fields[name] = ExpandableField(
                attr=orm_attr(name, field), loader=marker.loader
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
    hidden = frozenset(f.attr for f in expandable_fields.values()) & state.unloaded
    return handler(_HideUnloaded(data, hidden))
