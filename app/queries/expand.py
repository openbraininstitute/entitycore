"""Entity-wide `expand` support for on-demand derivation lists.

An ``expand`` value is ``name[:qualifier]``: for the derivation directions the qualifier is a
DerivationType, e.g. ``generated_from_derivations:circuit_extraction``. ``.`` is reserved for
future nested paths, and ``=`` for future keyed qualifiers (e.g. ``:label=...``).
"""

from collections.abc import Iterable, Set as AbstractSet
from enum import StrEnum, auto
from typing import TYPE_CHECKING, cast

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from app.db.model import Derivation, Entity, Identifiable
from app.db.types import DerivationType

_QUALIFIER_SEPARATOR = ":"
MEASUREMENT_ANNOTATION_EXPAND = "measurement_annotation"

EXPAND_DESCRIPTION = (
    "Related data to include. `generated_from_derivations` / `used_by_derivations` load all the "
    "derivations in that direction, `<direction>:<derivation_type>` only that type. "
    "Repeat to combine; a bare direction includes all types. "
    "The `generated_derivation__*` / `used_derivation__*` filters don't affect the loaded lists."
)


class DerivationExpandDirection(StrEnum):
    generated_from_derivations = auto()
    used_by_derivations = auto()


# None means all the derivation types.
type _DerivationExpand = dict[DerivationExpandDirection, frozenset[DerivationType] | None]

# direction -> (Entity relationship to the derivations, Derivation side with the other entity)
_DERIVATION_RELATIONSHIPS = {
    DerivationExpandDirection.generated_from_derivations: ("derivations_as_generated", "used"),
    DerivationExpandDirection.used_by_derivations: ("derivations_as_used", "generated"),
}


def _build_expand_enum(name: str, extra_values: Iterable[str] = ()) -> type[StrEnum]:
    """Build an ``expand`` enum with the bare and typed derivation values, plus extra values."""
    values = [
        *DerivationExpandDirection,
        *(
            f"{direction}{_QUALIFIER_SEPARATOR}{derivation_type}"
            for direction in DerivationExpandDirection
            for derivation_type in DerivationType
        ),
        *extra_values,
    ]
    members = [(value.replace(_QUALIFIER_SEPARATOR, "__"), value) for value in values]
    return cast("type[StrEnum]", StrEnum(name, members))


# Built dynamically from DerivationType; type checkers only see a StrEnum.
if TYPE_CHECKING:
    EntityExpand = StrEnum
    MeasurableEntityExpand = StrEnum
else:
    EntityExpand = _build_expand_enum("EntityExpand")
    MeasurableEntityExpand = _build_expand_enum(
        "MeasurableEntityExpand", extra_values=[MEASUREMENT_ANNOTATION_EXPAND]
    )


def _parse_derivation_expand(expand: AbstractSet[str] | None) -> _DerivationExpand:
    """Map the requested derivation directions to their types; a bare direction wins.

    Values that are not derivation directions (e.g. ``measurement_annotation``) are ignored.
    """
    requested: dict[DerivationExpandDirection, set[DerivationType] | None] = {}
    for value in expand or ():
        name, _, qualifier = value.partition(_QUALIFIER_SEPARATOR)
        if name not in DerivationExpandDirection:
            continue
        direction = DerivationExpandDirection(name)
        if not qualifier:
            requested[direction] = None
        elif (types := requested.setdefault(direction, set())) is not None:
            types.add(DerivationType(qualifier))
    return {
        direction: None if types is None else frozenset(types)
        for direction, types in requested.items()
    }


def apply_derivation_expand(
    query: sa.Select, db_model_class: type[Identifiable], expand: AbstractSet[str] | None
) -> sa.Select:
    """Eager-load the requested derivation directions onto an entity query.

    The specific ``selectinload`` overrides a service's ``raiseload("*")``, so an un-expanded
    direction stays unloaded and serializes as ``null``.
    """
    if not expand or not issubclass(db_model_class, Entity):
        return query
    for direction, types in _parse_derivation_expand(expand).items():
        relationship_name, related_name = _DERIVATION_RELATIONSHIPS[direction]
        relationship = getattr(db_model_class, relationship_name)
        if types is not None:
            relationship = relationship.and_(Derivation.derivation_type.in_(types))
        query = query.options(
            selectinload(relationship).joinedload(getattr(Derivation, related_name))
        )
    return query
