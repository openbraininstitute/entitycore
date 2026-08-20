"""Cached alias creation and helper functions for SQLAlchemy aliases."""

import functools
from collections.abc import Mapping
from typing import Any, cast

from sqlalchemy.orm import DeclarativeBase, aliased

type Aliases = Mapping[type[DeclarativeBase], Mapping[str, Any]]


@functools.cache
def get_alias[T: type[DeclarativeBase]](cls: T, name: str) -> T:
    """Return a cached SQLAlchemy alias for the given model class and name.

    The same `(cls, name)` pair always returns the same Python object (identity guarantee).
    Different pairs always return different objects.

    Args:
        cls: The SQLAlchemy model class to alias.
        name: A logical name for this alias (e.g. "used", "brain_region").

    Returns:
        An `aliased()` instance of `cls` with `flat=True`.
    """
    return cast("T", aliased(cls, flat=True, name=f"{name}_alias"))


def build_aliases(*pairs: tuple[type[DeclarativeBase], str]) -> Aliases:
    """Construct an Aliases mapping from `(ModelClass, name)` pairs using get_alias.

    Each pair calls `get_alias(model_cls, name)` to obtain the cached singleton.

    Args:
        *pairs: Tuples of (model_class, alias_name).

    Returns:
        A dict mapping model classes to their named aliases.
    """
    data: dict[type[DeclarativeBase], dict[str, Any]] = {}
    for model_cls, name in pairs:
        data.setdefault(model_cls, {})[name] = get_alias(model_cls, name)
    return data


def merge_aliases(a: Aliases, b: Aliases) -> Aliases:
    """Merge two Aliases mappings into a new one.

    If both contain aliases for the same model class, the name->alias dicts are merged
    (b's entries take precedence on key conflicts).

    Args:
        a: First aliases mapping.
        b: Second aliases mapping (takes precedence on conflicts).

    Returns:
        A new dict containing aliases from both.
    """
    merged: dict[type[DeclarativeBase], dict[str, Any]] = {k: dict(v) for k, v in a.items()}
    for cls, names in b.items():
        merged.setdefault(cls, {}).update(names)
    return merged
