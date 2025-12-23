from itertools import chain

import sqlalchemy as sa

from app.db.model import Identifiable
from app.filters.base import NESTED_SEPARATOR, CustomFilter
from app.logger import L
from app.queries.types import ApplyOperations


def _to_parts(s: str) -> list[str]:
    """Convert a dot-separated string to a list of substrings based on the dots.

    Examples:
        "a.b.c" -> ["a", "a.b", "a.b.c"]
    """
    parts = s.split(".")
    return [".".join(parts[: i + 1]) for i in range(len(parts))]


def _underscores_to_dots(names: list[str]) -> list[str]:
    """Convert double underscore string into dot-separated strings without field name.

    Examples:
        subject__species__name -> subject.species
    """
    return [".".join(name.split(NESTED_SEPARATOR)[:-1]) for name in names]


def filter_from_db[I: Identifiable](
    query: sa.Select,
    filter_model: CustomFilter[I],
    filter_joins: dict[str, ApplyOperations],
    forced_joins: set[str] | None = None,
) -> sa.Select:
    """Apply the required joins based on the filter.

    Args:
        query: select query.
        filter_model: filter model instance.
        filter_joins: dict of names and operations to apply to the query. The names should be
            valid names of nested filters, and it's possible to specify deeply nested filters using
            the dot notation, e.g. "measurement_annotation.measurement_kind".
        forced_joins: subset of keys of filter_joins, that are applied only if the corresponding
            nested filters have not been specified. This is useful to avoid duplicate joins.
    """
    forced_joins = set(chain.from_iterable(_to_parts(s) for s in forced_joins or ()))
    if diff := forced_joins.difference(filter_joins):
        msg = f"Not allowed in forced_joins: {diff}"
        raise RuntimeError(msg)

    ordering_joins = set(
        chain.from_iterable(
            _to_parts(s) for s in _underscores_to_dots(filter_model.nested_ordering_fields)
        )
    )

    for name, func in filter_joins.items():
        to_be_applied = (
            name in ordering_joins
            or filter_model.get_nested_filter(name)
            or filter_model.has_nested_filtering_field(name)
        )
        if (to_be_applied and not forced_joins) or (not to_be_applied and name in forced_joins):
            L.debug("Applying join filter for {!r}", name)
            query = func(query)
    return query
