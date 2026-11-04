"""Generic `expand` support: opt-in fields of the read schemas, loaded only when requested.

An ``expand`` value is a path relative to the returned item, with ``.`` between nested objects and
an optional ``:qualifier`` on the last segment, e.g. ``measurement_annotation``,
``generated_from_derivations:circuit_extraction``, or ``<relationship>.<field>``. A path implies
its expandable ancestors. ``=`` is reserved for future keyed qualifiers (e.g. ``:label=...``).

The fields are marked with `Expandable` in the read schemas (see `app.schemas.base`). The allowed
paths of a schema are computed by walking its fields and the mapper of the ORM model in parallel.
"""

import types
from collections.abc import Iterator, Sequence, Set as AbstractSet
from dataclasses import dataclass, field
from enum import StrEnum
from functools import cache
from typing import Annotated, Any, TypeAliasType, Union, cast, get_args, get_origin

import sqlalchemy as sa
from sqlalchemy.orm import (
    ColumnProperty,
    InstanceState,
    Load,
    Mapper,
    QueryableAttribute,
    RelationshipProperty,
)

from app.db.model import Entity, Identifiable
from app.schemas.base import Schema
from app.schemas.expand import ExpandableField, expand_load, expandable_fields

QUALIFIER_SEPARATOR = ":"
PATH_SEPARATOR = "."
MAX_EXPAND_DEPTH = 3

EXPAND_DESCRIPTION = (
    "Optional fields to include, returned only when requested. "
    "Use `<field>` for the item, `<relationship>.<field>` for nested objects, and "
    "`<field>:<qualifier>` where supported: `generated_from_derivations:<derivation_type>` and "
    "`used_by_derivations:<derivation_type>` load only that derivation type. "
    "Repeat to combine; a field without qualifier includes all the qualifiers. "
    "The `generated_derivation__*` / `used_derivation__*` filters don't affect the loaded lists."
)

# the schema of a response: a Schema class or a type alias of a union of Schema classes
type SchemaSpec = type[Schema] | TypeAliasType


def _schema_classes(annotation: Any) -> tuple[type[Schema], ...]:
    """Return the Schema classes in a field annotation or schema spec, unwrapping containers."""
    annotation = getattr(annotation, "__expand_schema__", annotation)
    if isinstance(annotation, TypeAliasType):
        return _schema_classes(annotation.__value__)
    origin = get_origin(annotation)
    if origin is Annotated:
        return _schema_classes(get_args(annotation)[0])
    if origin in {Union, types.UnionType, list, Sequence, set, frozenset, tuple}:
        return tuple(dict.fromkeys(c for arg in get_args(annotation) for c in _schema_classes(arg)))
    if isinstance(annotation, type) and issubclass(annotation, Schema):
        return (annotation,)
    return ()


@dataclass(frozen=True, slots=True, kw_only=True)
class _Field:
    name: str
    attr: str
    expandable: ExpandableField | None
    nested: tuple[type[Schema], ...]


def _find_field(schema_classes: Sequence[type[Schema]], name: str) -> _Field | None:
    for schema_class in schema_classes:
        field_info = schema_class.model_fields.get(name)
        if field_info is None:
            continue
        expandable = expandable_fields(schema_class).get(name)
        alias = field_info.validation_alias
        attr = expandable.attr if expandable else alias if isinstance(alias, str) else name
        return _Field(
            name=name,
            attr=attr,
            expandable=expandable,
            nested=_schema_classes(field_info.annotation),
        )
    return None


def _walk(
    schema_classes: tuple[type[Schema], ...],
    mapper: Mapper,
    prefix: str,
    depth: int,
    seen: tuple[type[Schema], ...],
) -> Iterator[str]:
    names = dict.fromkeys(name for c in schema_classes for name in c.model_fields)
    for name in names:
        schema_field = cast("_Field", _find_field(schema_classes, name))
        prop = mapper.attrs.get(schema_field.attr)
        expandable = schema_field.expandable
        path = f"{prefix}{name}"
        if expandable:
            marker = expandable.marker
            if prop is None:
                msg = f"{path}: no ORM attribute {schema_field.attr!r} on {mapper.class_.__name__}"
                raise TypeError(msg)
            if (
                isinstance(prop, RelationshipProperty)
                and issubclass(prop.mapper.class_, Entity)
                and marker.loader is None
            ):
                # the related entities must be filtered by authorization, by a loader
                msg = f"{path}: expandable relationships to entities require a loader"
                raise TypeError(msg)
            yield path
            yield from (f"{path}{QUALIFIER_SEPARATOR}{q}" for q in marker.qualifiers)
            if marker.loader:
                # a custom loader decides what is loaded below the field
                continue
        if (
            isinstance(prop, RelationshipProperty)
            and depth < MAX_EXPAND_DEPTH
            and len(schema_field.nested) == 1
            and schema_field.nested[0] not in seen
        ):
            nested = schema_field.nested
            yield from _walk(
                nested, prop.mapper, f"{path}{PATH_SEPARATOR}", depth + 1, seen + nested
            )


@cache
def allowed_expand_paths(schema: SchemaSpec, db_model_class: type[Identifiable]) -> tuple[str, ...]:
    """Return the allowed expand values of the schema returned for db_model_class.

    Example:
        >>> allowed_expand_paths(CircuitRead, Circuit)
        ('generated_from_derivations', 'generated_from_derivations:circuit_extraction', ...)
    """
    schema_classes = _schema_classes(schema)
    if not schema_classes:
        msg = f"{schema} is not a Schema"
        raise TypeError(msg)
    mapper = sa.inspect(db_model_class)
    return tuple(dict.fromkeys(_walk(schema_classes, mapper, "", 1, schema_classes)))


def _member_name(value: str) -> str:
    return value.replace(PATH_SEPARATOR, "___").replace(QUALIFIER_SEPARATOR, "__")


@cache
def expand_enum(schema: SchemaSpec, db_model_class: type[Identifiable]) -> type[StrEnum]:
    """Return the StrEnum of the allowed expand values, named after the schema.

    Example:
        >>> expand_enum(CircuitRead, Circuit).__name__
        'CircuitReadExpand'
    """
    values = allowed_expand_paths(schema, db_model_class)
    if not values:
        msg = f"{schema} has no expandable fields"
        raise TypeError(msg)
    name = f"{schema.__name__}Expand"
    return cast("type[StrEnum]", StrEnum(name, [(_member_name(v), v) for v in values]))


@dataclass(kw_only=True)
class _Node:
    """Requested expand paths, as a tree of field names."""

    bare: bool = False  # requested without qualifier
    qualifiers: set[str] = field(default_factory=set)
    children: dict[str, _Node] = field(default_factory=dict)

    def requested_qualifiers(self) -> frozenset[str] | None:
        """Return the requested qualifiers, or None for all (a value without qualifier wins)."""
        return None if self.bare or not self.qualifiers else frozenset(self.qualifiers)


def _build_tree(expand: AbstractSet[str]) -> _Node:
    root = _Node()
    for value in expand:
        path, _, qualifier = value.partition(QUALIFIER_SEPARATOR)
        node = root
        for segment in path.split(PATH_SEPARATOR):
            node = node.children.setdefault(segment, _Node())
        if qualifier:
            node.qualifiers.add(qualifier)
        else:
            node.bare = True
    return root


def _loader_options(
    node: _Node,
    schema_classes: tuple[type[Schema], ...],
    model_class: type,
    parent: Load | None,
    path: str,
) -> Iterator[Load]:
    for name, child in node.children.items():
        child_path = f"{path}{name}"
        schema_field = _find_field(schema_classes, name)
        attr = getattr(model_class, schema_field.attr, None) if schema_field else None
        prop = attr.property if isinstance(attr, QueryableAttribute) else None
        if schema_field is None or attr is None or prop is None:
            msg = f"Invalid expand path: {child_path}"
            raise ValueError(msg)
        expandable = schema_field.expandable
        loader = expandable.marker.loader if expandable else None
        if isinstance(prop, ColumnProperty) or loader:
            if expandable is None or child.children:
                msg = f"Invalid expand path: {child_path}"
                raise ValueError(msg)
            if loader:
                yield from loader(parent, attr, child.requested_qualifiers())
            else:
                yield expand_load(parent, "undefer", attr)
            continue
        if expandable:
            load = expand_load(parent, "selectinload", attr)
            # the nested relationships of the expanded objects must be loaded explicitly
            yield load.raiseload("*")
        else:
            load = expand_load(parent, "defaultload", attr)
        yield from _loader_options(
            child, schema_field.nested, prop.mapper.class_, load, f"{child_path}{PATH_SEPARATOR}"
        )


def apply_expand(
    query: sa.Select,
    db_model_class: type[Identifiable],
    schema: object,
    expand: AbstractSet[str] | None,
) -> sa.Select:
    """Add to the query the loader options of the requested expand paths.

    schema is the response schema (see `SchemaSpec`). The values must be already validated
    (e.g. with the enum of `expand_enum`). The specific loader options override a
    `raiseload("*")` added by the service.

    Example:
        >>> apply_expand(query, Circuit, CircuitRead, {"used_by_derivations:circuit_extraction"})
    """
    if not expand:
        return query
    options = list(
        _loader_options(_build_tree(expand), _schema_classes(schema), db_model_class, None, "")
    )
    return query.options(*options) if options else query


def unrequested_loaded_attrs(
    instance: object, schema: object, expand: AbstractSet[str] | None
) -> list[str]:
    """Return the ORM attributes of the top-level expandable fields loaded but not requested.

    Used to expire them after an update, e.g. a column set by the PATCH.
    """
    requested = {
        value.partition(QUALIFIER_SEPARATOR)[0].partition(PATH_SEPARATOR)[0]
        for value in expand or ()
    }
    unloaded = cast("InstanceState", sa.inspect(instance)).unloaded
    attrs = {
        expandable.attr
        for schema_class in _schema_classes(schema)
        for expandable in expandable_fields(schema_class).values()
        if expandable.name not in requested
    }
    return sorted(attrs - unloaded)
