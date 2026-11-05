"""Generic `expand` support: opt-in fields of the read schemas, loaded only when requested.

An ``expand`` value is a path relative to the returned item, with ``.`` between nested objects and
an optional ``:qualifier`` on the last segment, e.g. ``measurement_annotation``,
``generated_from_derivations:circuit_extraction``, or ``<relationship>.<field>``. A path implies
its expandable ancestors. ``=`` is reserved for future keyed qualifiers (e.g. ``:label=...``).

The fields are marked with `Expandable` in the read schemas (see `app.schemas.expand`), and the
fields needing more than a loader strategy name a custom loader of `app.queries.expand_loaders`.
At startup, the schema and the mapper of the ORM model are walked in parallel to build a plan for
each allowed path (`_ExpandPlan`): how to load each segment, from the root of the query. The plans
give both the allowed values (the `expand` enums) and, per request, the loader options of the
requested paths, so the two can't disagree.
"""

import types
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from typing import Annotated, Any, TypeAliasType, Union, cast, get_args, get_origin

import sqlalchemy as sa
from sqlalchemy.orm import (
    ColumnProperty,
    InstanceState,
    Load,
    Mapper,
    MapperProperty,
    QueryableAttribute,
    RelationshipProperty,
)

from app.db.model import Entity, Identifiable
from app.queries.expand_loaders import CUSTOM_LOADERS, ExpandLoader, LoaderStrategy, expand_load
from app.queries.types import SupportsModelValidate
from app.schemas.base import Schema
from app.schemas.expand import ExpandableField, orm_attr

QUALIFIER_SEPARATOR = ":"
PATH_SEPARATOR = "."
# maximum number of segments of a path, to keep the enums small
MAX_EXPAND_DEPTH = 3

EXPAND_DESCRIPTION = (
    "Optional fields to include. Repeat to request several; `<field>:<qualifier>` narrows a "
    "field (e.g. a derivation type), and a field without qualifier includes all."
)

# the schema of a response: a Schema class or a type alias of a union of Schema classes
type SchemaSpec = type[Schema] | TypeAliasType

# the requested expand values, already validated (see `expand_query` in `app.dependencies.common`)
ExpandPaths = frozenset[str]


def _schema_classes(annotation: Any) -> tuple[type[Schema], ...]:
    """Return the Schema classes in a field annotation or schema spec, unwrapping containers.

    A class can declare the schema to walk in `__expand_schema__`, e.g. a TypeAdapter wrapper of
    a union of schemas.
    """
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
    """A field of a schema, as needed to walk it.

    Attributes:
        attr: name of the ORM attribute (see `orm_attr`).
        expandable: the expandable field, or None if always returned.
        nested: the Schema classes in the type of the field, to walk the nested paths.
    """

    attr: str
    expandable: ExpandableField | None
    nested: tuple[type[Schema], ...]


def _find_field(schema_classes: Sequence[type[Schema]], name: str) -> _Field:
    """Return the schema field `name` of the first schema class declaring it.

    In a union of schemas, the first class decides whether the field is expandable: the current
    unions share their expandable fields through the same mixins.
    """
    schema_class = next(c for c in schema_classes if name in c.model_fields)
    field_info = schema_class.model_fields[name]
    return _Field(
        attr=orm_attr(name, field_info),
        expandable=schema_class.__expandable_fields__.get(name),
        nested=_schema_classes(field_info.annotation),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class _Step:
    """Loading of one segment of an expand path with a loader strategy.

    Below an expandable relationship (`selectinload`), the nested relationships raise unless
    loaded explicitly, instead of being lazy loaded for each object.
    """

    attr: QueryableAttribute
    strategy: LoaderStrategy


@dataclass(frozen=True, slots=True, kw_only=True)
class _CustomLoad:
    """Loading of an expandable field by its custom loader, after the steps of its ancestors."""

    attr: QueryableAttribute
    loader: ExpandLoader


@dataclass(frozen=True, slots=True, kw_only=True)
class _ExpandPlan:
    """Loading of an expand path, from the root of the query, and its accepted qualifiers.

    Examples, with `CircuitRead` and with a nested deferred column `species.embedding`:
        generated_from_derivations: steps=(), custom=<derivation loader>, qualifiers=<types>
        species.embedding: steps=(defaultload(species), undefer(embedding)), custom=None
    """

    steps: tuple[_Step, ...]  # the ancestors, and the field unless it has a custom loader
    custom: _CustomLoad | None = None
    qualifiers: tuple[str, ...] = ()


def _expandable_strategy(path: str, prop: MapperProperty) -> LoaderStrategy:
    """Return the strategy loading an expandable field without custom loader."""
    if isinstance(prop, ColumnProperty):
        return "undefer"
    if issubclass(prop.mapper.class_, Entity):
        # the related entities must be filtered by authorization, by a custom loader
        msg = f"{path}: expandable relationships to entities require a custom loader"
        raise TypeError(msg)
    return "selectinload"


def _walk(
    schema_classes: tuple[type[Schema], ...],
    mapper: Mapper,
    prefix: str,
    steps: tuple[_Step, ...],
    seen: frozenset[type[Schema]],
) -> Iterator[tuple[str, _ExpandPlan]]:
    """Yield the allowed paths below prefix, with their plans."""
    names = dict.fromkeys(name for c in schema_classes for name in c.model_fields)
    for name in names:
        schema_field = _find_field(schema_classes, name)
        path = f"{prefix}{name}"
        prop = mapper.attrs.get(schema_field.attr)
        if expandable := schema_field.expandable:
            if prop is None:
                msg = f"{path}: no ORM attribute {schema_field.attr!r} on {mapper.class_.__name__}"
                raise TypeError(msg)
            attr = getattr(mapper.class_, schema_field.attr)
            if expandable.loader is not None:
                custom = CUSTOM_LOADERS[expandable.loader]
                # the custom loader decides what is loaded below the field: no nested paths
                custom_load = _CustomLoad(attr=attr, loader=custom.load)
                yield (
                    path,
                    _ExpandPlan(steps=steps, custom=custom_load, qualifiers=custom.qualifiers),
                )
                continue
            step = _Step(attr=attr, strategy=_expandable_strategy(path, prop))
            yield path, _ExpandPlan(steps=(*steps, step))
            if not isinstance(prop, RelationshipProperty):
                continue  # no nested paths below a column
        elif isinstance(prop, RelationshipProperty):
            # traversed to reach nested expandable fields, keeping the strategy of the service
            step = _Step(attr=getattr(mapper.class_, schema_field.attr), strategy="defaultload")
        else:
            continue  # neither expandable nor a relationship: nothing to offer
        # walk the nested schema of the relationship, if any
        if (
            len(steps) + 1 < MAX_EXPAND_DEPTH
            # not walked: the members of a union of schemas can declare different fields
            and len(schema_field.nested) == 1
            and schema_field.nested[0] not in seen  # cycle guard
        ):
            nested = schema_field.nested
            yield from _walk(
                nested, prop.mapper, f"{path}{PATH_SEPARATOR}", (*steps, step), seen | set(nested)
            )


@cache
def _expand_plans(
    schema: SchemaSpec | SupportsModelValidate, db_model_class: type[Identifiable]
) -> Mapping[str, _ExpandPlan]:
    """Return the plans of the allowed paths (without qualifier) of schema."""
    schema_classes = _schema_classes(schema)
    if not schema_classes:
        msg = f"{schema} is not a Schema"
        raise TypeError(msg)
    mapper = sa.inspect(db_model_class)
    return dict(_walk(schema_classes, mapper, "", (), frozenset(schema_classes)))


@cache
def allowed_expand_paths(schema: SchemaSpec, db_model_class: type[Identifiable]) -> tuple[str, ...]:
    """Return the allowed expand values of the schema returned for db_model_class.

    Example:
        >>> allowed_expand_paths(CircuitRead, Circuit)
        ('generated_from_derivations', 'generated_from_derivations:circuit_extraction', ...)
    """
    return tuple(
        value
        for path, plan in _expand_plans(schema, db_model_class).items()
        for value in (path, *(f"{path}{QUALIFIER_SEPARATOR}{q}" for q in plan.qualifiers))
    )


def _member_name(value: str) -> str:
    # enum member names must be identifiers; different replacements keep them unique
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


def _requested_qualifiers(expand: Iterable[str]) -> dict[str, frozenset[str] | None]:
    """Group the expand values by path: the requested qualifiers, or None for all of them.

    A value without qualifier wins over the values with qualifiers of the same path.
    """
    requested: dict[str, set[str] | None] = {}
    for value in expand:
        path, _, qualifier = value.partition(QUALIFIER_SEPARATOR)
        if not qualifier:
            requested[path] = None
        elif (qualifiers := requested.setdefault(path, set())) is not None:
            qualifiers.add(qualifier)
    return {path: None if q is None else frozenset(q) for path, q in requested.items()}


def _plan_options(plan: _ExpandPlan, qualifiers: frozenset[str] | None) -> Iterator[Load]:
    """Yield the loader options of a plan, chaining its steps from the root of the query."""
    load: Load | None = None
    for step in plan.steps:
        load = expand_load(load, step.strategy, step.attr)
        if step.strategy == "selectinload":
            yield load.raiseload("*")
    if plan.custom:
        yield from plan.custom.loader(load, plan.custom.attr, qualifiers)
    else:
        yield cast("Load", load)  # without a custom loader, a plan has at least one step


def apply_expand(
    query: sa.Select,
    db_model_class: type[Identifiable],
    schema: SchemaSpec | SupportsModelValidate,
    expand: ExpandPaths | None,
) -> sa.Select:
    """Add to the query the loader options of the requested expand paths.

    The values must be already validated (e.g. with the enum of `expand_enum`), only the paths
    are checked. The specific loader options override a `raiseload("*")` added by the service,
    and the options of paths sharing ancestors are merged by SQLAlchemy.

    Raises:
        ValueError: if a path is not allowed for schema.

    Example:
        >>> apply_expand(
        ...     query, Circuit, CircuitRead, frozenset({"used_by_derivations:circuit_extraction"})
        ... )
    """
    if not expand:
        return query
    plans = _expand_plans(schema, db_model_class)
    options = []
    for path, qualifiers in _requested_qualifiers(expand).items():
        if (plan := plans.get(path)) is None:
            msg = f"Invalid expand path: {path}"
            raise ValueError(msg)
        options.extend(_plan_options(plan, qualifiers))
    return query.options(*options)


def unrequested_loaded_attrs(
    instance: object, schema: SchemaSpec | SupportsModelValidate, expand: ExpandPaths | None
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
        for name, expandable in schema_class.__expandable_fields__.items()
        if name not in requested
    }
    return sorted(attrs - unloaded)
