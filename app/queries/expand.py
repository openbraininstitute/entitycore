"""Shared, entity-wide `expand` support for on-demand derivation lists.

Every entity read schema carries the load-aware ``generated_from_derivations`` /
``used_by_derivations`` fields (see app.schemas.entity.DerivationReadMixin); they serialize as
``null`` unless the matching direction was eagerly loaded. This module centralizes the enum the
read endpoints expose as the ``expand`` query param and the loader options that populate the
relationships.
"""

from collections.abc import Set as AbstractSet
from enum import StrEnum, auto

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from app.db.model import Derivation, Entity, Identifiable


class EntityExpand(StrEnum):
    """Derivation lists that any entity endpoint can load on demand via ``?expand=``."""

    generated_from_derivations = auto()
    used_by_derivations = auto()


def apply_derivation_expand(
    query: sa.Select, db_model_class: type[Identifiable], expand: AbstractSet[str] | None
) -> sa.Select:
    """Eager-load the requested derivation directions onto an entity query.

    A no-op for non-entity models and when nothing is requested. Adding the specific
    ``selectinload`` after a service's ``raiseload("*")`` is intentional: the more specific path
    overrides the wildcard, so an un-expanded direction stays unloaded and its load-aware property
    returns ``None`` instead of tripping ``raiseload``.
    """
    if not expand or not issubclass(db_model_class, Entity):
        return query
    if EntityExpand.generated_from_derivations in expand:
        query = query.options(
            selectinload(db_model_class.derivations_as_generated).joinedload(Derivation.used)
        )
    if EntityExpand.used_by_derivations in expand:
        query = query.options(
            selectinload(db_model_class.derivations_as_used).joinedload(Derivation.generated)
        )
    return query
