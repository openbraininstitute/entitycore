"""Loading of the expandable fields (see `app.queries.expand`).

Most expandable fields are loaded with a loader strategy (`undefer`, `selectinload`). The fields
needing more, e.g. nested relationships of the related objects or qualifiers, name a custom loader
in their `Expandable` marker, defined in `CUSTOM_LOADERS`.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from sqlalchemy import orm

from app.db.types import DerivationType
from app.schemas.expand import ExpandLoaderName

type LoaderStrategy = Literal["defaultload", "joinedload", "selectinload", "undefer"]


def expand_load(parent: orm.Load | None, strategy: LoaderStrategy, attr: Any) -> orm.Load:
    """Return the loader option `strategy` for attr, chained to parent (None at the root).

    Strategies:
        selectinload: relationships, loaded with a second query (preferred for lists).
        joinedload: single-object relationships, loaded with a join in the same query.
        defaultload: traverse a relationship keeping its loading strategy, to reach
            nested attributes.
        undefer: deferred columns.

    See https://docs.sqlalchemy.org/en/21/orm/queryguide/relationships.html and
    https://docs.sqlalchemy.org/en/21/orm/queryguide/columns.html.

    Example:
        >>> expand_load(None, "selectinload", Entity.assets)  # selectinload(Entity.assets)
    """
    if parent is None:
        return getattr(orm, strategy)(attr)
    return getattr(parent, strategy)(attr)


class ExpandLoader(Protocol):
    """Builds the loader options of an expandable field with a custom loader."""

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
class CustomLoader:
    """Custom loading of the expandable fields naming it in their `Expandable` marker.

    Attributes:
        load: builder of the loader options.
        qualifiers: values accepted after `:` in the expand values of the field.
    """

    load: ExpandLoader
    qualifiers: tuple[str, ...] = ()


def _derivation_loader(other_side: str) -> ExpandLoader:
    """Return the loader of a derivation list, with the entity on the other side of each one.

    The qualifiers are the derivation types to load.
    """

    def load(
        parent: orm.Load | None, attr: orm.QueryableAttribute, qualifiers: frozenset[str] | None
    ) -> list[orm.Load]:
        derivation_class = attr.property.mapper.class_
        if qualifiers is not None:
            derivation_types = [DerivationType(q) for q in qualifiers]
            attr = attr.and_(derivation_class.derivation_type.in_(derivation_types))
        other_entity = getattr(derivation_class, other_side)
        return [expand_load(parent, "selectinload", attr).joinedload(other_entity)]

    return load


def _measurement_annotation_loader(
    parent: orm.Load | None, attr: orm.QueryableAttribute, _qualifiers: frozenset[str] | None
) -> list[orm.Load]:
    """Load the measurement annotation of an entity, with its kinds, items and labels."""
    annotation_class = attr.property.mapper.class_
    kind_class = annotation_class.measurement_kinds.property.mapper.class_
    load = expand_load(parent, "joinedload", attr)
    # `entity_type` reads the annotated entity: at the root of the query it's the queried row
    entity_load = (
        load.contains_eager(annotation_class.entity)
        if parent is None
        else load.selectinload(annotation_class.entity)
    )
    return [
        load.selectinload(annotation_class.measurement_kinds).options(
            orm.selectinload(kind_class.measurement_items),
            orm.selectinload(kind_class.measurement_label),
        ),
        entity_load,
    ]


CUSTOM_LOADERS: Mapping[ExpandLoaderName, CustomLoader] = {
    "generated_derivations": CustomLoader(
        load=_derivation_loader("used"), qualifiers=tuple(DerivationType)
    ),
    "used_derivations": CustomLoader(
        load=_derivation_loader("generated"), qualifiers=tuple(DerivationType)
    ),
    "measurement_annotation": CustomLoader(load=_measurement_annotation_loader),
}
