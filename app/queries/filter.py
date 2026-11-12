from collections.abc import Iterable
from itertools import chain

import sqlalchemy as sa
from sqlalchemy.sql import operators

from app.db.model import Identifiable
from app.filters.base import NESTED_SEPARATOR, CustomFilter
from app.logger import L
from app.queries.types import ApplyOperations, JoinSpecMap
from app.queries.utils import expand_dotted_key


def _underscores_to_dots(names: list[str]) -> list[str]:
    """Convert double underscore string into dot-separated strings without field name.

    Examples:
        subject__species__name -> subject.species
    """
    return [".".join(name.split(NESTED_SEPARATOR)[:-1]) for name in names]


def _apply_outer_join(query: sa.Select, apply_join: ApplyOperations) -> sa.Select:
    """Apply the join, and turn into outer joins the ones that it added.

    Facets are computed together in a single query, so a facet join cannot discard the rows
    without a match, because they are still needed by the other facets.
    """
    num_joins = len(query._setup_joins)  # ruff:ignore[private-member-access]
    new_query = apply_join(query)
    setup_joins = new_query._setup_joins  # ruff:ignore[private-member-access]
    new_query._setup_joins = (  # ruff:ignore[private-member-access]
        *setup_joins[:num_joins],
        *(
            (target, onclause, from_, {**flags, "isouter": True})
            for target, onclause, from_, flags in setup_joins[num_joins:]
        ),
    )
    return new_query


def _is_single_valued_join(target: object, onclause: object) -> bool:
    """Return True if the join matches at most one row of the target for each row on the left.

    That happens if the join condition is an equality with the primary key of the target.
    When unsure, return False.
    """
    if not (isinstance(onclause, sa.BinaryExpression) and onclause.operator is operators.eq):
        return False
    target_inspection = sa.inspect(target, raiseerr=False)
    selectable = getattr(target_inspection, "selectable", target)
    if not isinstance(selectable, sa.FromClause):
        return False
    return any(
        isinstance(column, sa.ColumnClause)
        and column.primary_key
        and column.table is not None
        # a column of a composite primary key doesn't identify a single row
        and sum(1 for _ in column.table.primary_key) == 1  # pyright: ignore[reportAttributeAccessIssue]
        and selectable.is_derived_from(column.table)
        for column in (onclause.left, onclause.right)
    )


def multi_valued_facet_keys(
    query: sa.Select, join_specs: JoinSpecMap, facet_keys: Iterable[str]
) -> set[str]:
    """Return the facet keys that can multiply the rows of the query, because of a one-to-many join.

    The keys with an ancestor that is multi-valued are included, since they need its join.
    Any key that is not recognized as single-valued is considered multi-valued.
    """
    multi_valued = set()
    for name, spec in join_specs.items():
        num_joins = len(query._setup_joins)  # ruff:ignore[private-member-access]
        new_joins = spec.apply_facet_join(query)._setup_joins[num_joins:]  # ruff:ignore[private-member-access]
        if not all(_is_single_valued_join(t, on) for t, on, _, _ in new_joins):
            multi_valued.add(name)
    return {key for key in facet_keys if multi_valued.intersection(expand_dotted_key(key))}


def filter_from_db[I: Identifiable](
    query: sa.Select,
    filter_model: CustomFilter[I],
    join_specs: JoinSpecMap,
    *,
    facet_keys: Iterable[str] = (),
) -> sa.Select:
    """Apply the required joins based on the filter.

    For filtering: uses spec.apply_filter_join (inner join).
    For sorting: uses spec.apply_join (outer join).
    For facets: uses spec.apply_facet_join for the facet key and its ancestors.

    Args:
        query: select query.
        filter_model: filter model instance.
        join_specs: dict of names to JoinSpec. The names should be valid names of nested filters,
            and it's possible to specify deeply nested filters using the dot notation,
            e.g. "measurement_annotation.measurement_kind".
        facet_keys: optional facet keys whose joins must be applied for computing the facet labels.
            Expanded to include ancestor keys (e.g. "subject.species" -> {"subject",
            "subject.species"}). Takes priority over filter/sort joins for the same key.
    """
    expanded_facet_keys = set(chain.from_iterable(expand_dotted_key(k) for k in facet_keys))
    if diff := expanded_facet_keys.difference(join_specs):
        msg = f"Not allowed as facet_key: {diff}"
        raise RuntimeError(msg)

    ordering_joins = set(
        chain.from_iterable(
            expand_dotted_key(s) for s in _underscores_to_dots(filter_model.nested_ordering_fields)
        )
    )

    for name, spec in join_specs.items():
        is_filter = filter_model.get_nested_filter(name) or filter_model.has_nested_filtering_field(
            name
        )
        is_sort = name in ordering_joins
        is_facet = name in expanded_facet_keys
        if is_facet:
            L.debug("Applying facet join for {!r}", name)
            query = _apply_outer_join(query, spec.apply_facet_join)
        elif is_filter:
            L.debug("Applying filter join for {!r}", name)
            query = spec.apply_filter_join(query)
        elif is_sort:
            L.debug("Applying sort join for {!r}", name)
            query = spec.apply_join(query)
    return query
