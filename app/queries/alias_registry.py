"""Cached alias creation and helper functions for SQLAlchemy aliases.

This module provides:
- `get_alias(cls, name)`: A cached helper that returns a singleton `aliased()` instance
  per `(cls, name)` pair. Thread-safe, bounded cache.
- `Aliases`: A type alias for the per-endpoint alias mapping.
- `build_aliases(*pairs)`: Construct an Aliases dict from `(ModelClass, name)` pairs.
- `merge_aliases(a, b)`: Merge two Aliases dicts into a new one.

Examples:
    >>> from app.db.model import Entity
    >>> alias = get_alias(Entity, "used")
    >>> alias is get_alias(Entity, "used")
    True

    >>> aliases = build_aliases((Entity, "used"), (Entity, "generated"))
    >>> aliases[Entity]["used"] is get_alias(Entity, "used")
    True
"""

import functools
from collections.abc import Mapping
from typing import Any, cast

from sqlalchemy.orm import DeclarativeBase, aliased

type Aliases = Mapping[type[DeclarativeBase], Mapping[str, Any]]


@functools.lru_cache(maxsize=512)
def get_alias[T: type[DeclarativeBase]](cls: T, name: str) -> T:  # ruff:ignore[unused-function-argument]
    """Return a cached SQLAlchemy alias for the given model class and name.

    The same `(cls, name)` pair always returns the same Python object (identity guarantee).
    Different pairs always return different objects. The `name` parameter is used as a cache
    key discriminator — different names produce distinct alias objects.

    Args:
        cls: The SQLAlchemy model class to alias.
        name: A logical name for this alias (e.g. "used", "brain_region").
            Used as part of the cache key, not as the SQL alias name.

    Returns:
        An `aliased()` instance of `cls` with `flat=True`.

    Examples:
        >>> from app.db.model import Entity
        >>> a = get_alias(Entity, "used")
        >>> b = get_alias(Entity, "used")
        >>> a is b
        True
    """
    return cast("T", aliased(cls, flat=True))


def build_aliases(*pairs: tuple[type[DeclarativeBase], str]) -> Aliases:
    """Construct an Aliases mapping from `(ModelClass, name)` pairs using get_alias.

    Each pair calls `get_alias(model_cls, name)` to obtain the cached singleton.

    Args:
        *pairs: Tuples of (model_class, alias_name).

    Returns:
        A dict mapping model classes to their named aliases.

    Examples:
        >>> from app.db.model import Entity
        >>> aliases = build_aliases((Entity, "used"), (Entity, "generated"))
        >>> aliases[Entity]["used"] is get_alias(Entity, "used")
        True
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

    Examples:
        >>> from app.db.model import Entity, BrainRegion
        >>> a = build_aliases((Entity, "used"))
        >>> b = build_aliases((Entity, "generated"), (BrainRegion, "br"))
        >>> merged = merge_aliases(a, b)
        >>> sorted(merged[Entity].keys())
        ['generated', 'used']
    """
    merged: dict[type[DeclarativeBase], dict[str, Any]] = {k: dict(v) for k, v in a.items()}
    for cls, names in b.items():
        merged.setdefault(cls, {}).update(names)
    return merged
