"""Loading of the expandable fields (see `app.queries.expand`).

Most expandable fields are loaded with a loader strategy (`undefer`, `selectinload`). The fields
needing more, e.g. nested relationships of the related objects or qualifiers, name a custom loader
in their `Expandable` marker, defined in `CUSTOM_LOADERS`.
"""

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from sqlalchemy import orm

from app.db.auth import is_public_or_in_projects
from app.db.model import Base
from app.db.types import DERIVATION_TYPE_RULES, DerivationType, EntityType
from app.db.utils import ENTITY_TYPE_TO_CLASS
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


@dataclass(frozen=True, slots=True, kw_only=True)
class ExpandContext:
    """Authorization of the entities loaded by the custom loaders, e.g. the linked entities.

    The linked entities are filtered with the project that authorized the returned item.

    Attributes:
        check_authorized_project: whether to return only the entities that are public or in
            project_id (False in the admin endpoints).
        project_id: the project that authorized the returned item, or None for public only.

    Example:
        >>> ExpandContext(check_authorized_project=True, project_id=project_id)
    """

    check_authorized_project: bool
    project_id: uuid.UUID | None = None


class ExpandLoader(Protocol):
    """Builds the loader options of an expandable field with a custom loader."""

    def __call__(
        self,
        parent: orm.Load | None,
        attr: orm.QueryableAttribute,
        qualifiers: frozenset[str] | None,
        context: ExpandContext,
        /,
    ) -> Sequence[orm.Load]:
        """Return the loader options of the field.

        Args:
            parent: load of the parent object, or None at the root of the query.
            attr: ORM attribute of the field.
            qualifiers: requested qualifiers, or None when requested without qualifier.
            context: authorization of the loaded entities.

        Example:
            >>> def load(parent, attr, qualifiers, context):
            ...     return [expand_load(parent, "selectinload", attr)]
        """
        ...


class ExpandQualifiers(Protocol):
    """Returns the qualifiers accepted by an expandable field with a custom loader."""

    def __call__(self, db_model_class: type[Base], /) -> tuple[str, ...]:
        """Return the qualifiers accepted after `:` in the expand values of the field.

        Called when the expand plans are built, at startup.

        Args:
            db_model_class: ORM class declaring the field, at the level of the path.

        Example:
            >>> def qualifiers(db_model_class):
            ...     return ("circuit_extraction",) if db_model_class is Circuit else ()
        """
        ...


def _no_qualifiers(_db_model_class: type[Base], /) -> tuple[str, ...]:
    return ()


@dataclass(frozen=True, slots=True, kw_only=True)
class CustomLoader:
    """Custom loading of the expandable fields naming it in their `Expandable` marker.

    Attributes:
        load: builder of the loader options.
        qualifiers: returns the values accepted after `:` in the expand values of the field.
    """

    load: ExpandLoader
    qualifiers: ExpandQualifiers = _no_qualifiers


def _entity_types(db_model_class: type[Base]) -> frozenset[EntityType]:
    """Return the entity types of an ORM class and of its subclasses.

    Raises:
        TypeError: if db_model_class isn't an entity class.

    Example:
        >>> _entity_types(ElectricalRecording)
        frozenset({'electrical_recording', 'electrical_cell_recording', 'ion_channel_recording'})
    """
    entity_types = frozenset(
        entity_type
        for entity_type, entity_class in ENTITY_TYPE_TO_CLASS.items()
        if issubclass(entity_class, db_model_class)
    )
    if not entity_types:
        msg = f"{db_model_class.__name__} is not an entity class"
        raise TypeError(msg)
    return entity_types


def _derivation_types(side: Literal["used", "generated"]) -> ExpandQualifiers:
    """Return the qualifiers of a derivation list: the types allowing the entity on side."""

    def qualifiers(db_model_class: type[Base], /) -> tuple[str, ...]:
        entity_types = _entity_types(db_model_class)
        return tuple(
            derivation_type
            for derivation_type in DerivationType
            # None: any entity type is allowed on that side
            if (allowed := getattr(DERIVATION_TYPE_RULES[derivation_type], side)) is None
            or allowed & entity_types
        )

    return qualifiers


def _derivation_loader(other_side: str) -> ExpandLoader:
    """Return the loader of a derivation list, with the entity on the other side of each one.

    The qualifiers are the derivation types to load. With `check_authorized_project`, only the
    derivations whose other entity is public or in `project_id` are loaded.
    """

    def load(
        parent: orm.Load | None,
        attr: orm.QueryableAttribute,
        qualifiers: frozenset[str] | None,
        context: ExpandContext,
    ) -> list[orm.Load]:
        derivation_class = attr.property.mapper.class_
        other_entity = getattr(derivation_class, other_side)
        criteria = []
        if qualifiers is not None:
            derivation_types = [DerivationType(q) for q in qualifiers]
            criteria.append(derivation_class.derivation_type.in_(derivation_types))
        if context.check_authorized_project:
            # aliased, so that the EXISTS subquery can't correlate with the parent entity
            other_alias = orm.aliased(other_entity.property.mapper.class_, flat=True)
            project_ids = [context.project_id] if context.project_id else []
            criteria.append(
                other_entity.of_type(other_alias).has(
                    is_public_or_in_projects(other_alias, project_ids)
                )
            )
        if criteria:
            attr = attr.and_(*criteria)
        return [expand_load(parent, "selectinload", attr).joinedload(other_entity)]

    return load


def _measurement_annotation_loader(
    parent: orm.Load | None,
    attr: orm.QueryableAttribute,
    _qualifiers: frozenset[str] | None,
    _context: ExpandContext,
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
    "generated_from_derivations": CustomLoader(
        load=_derivation_loader("used"), qualifiers=_derivation_types("generated")
    ),
    "used_by_derivations": CustomLoader(
        load=_derivation_loader("generated"), qualifiers=_derivation_types("used")
    ),
    "measurement_annotation": CustomLoader(load=_measurement_annotation_loader),
}
