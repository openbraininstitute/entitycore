from itertools import chain

import sqlalchemy as sa

from app.db.model import Identifiable
from app.filters.base import NESTED_SEPARATOR, CustomFilter
from app.logger import L
from app.queries.types import JoinSpecMap
from app.queries.utils import expand_dotted_key


def _underscores_to_dots(names: list[str]) -> list[str]:
    """Convert double underscore string into dot-separated strings without field name.

    Examples:
        subject__species__name -> subject.species
    """
    return [".".join(name.split(NESTED_SEPARATOR)[:-1]) for name in names]


def filter_from_db[I: Identifiable](
    query: sa.Select,
    filter_model: CustomFilter[I],
    join_specs: JoinSpecMap,
    *,
    facet_key: str | None = None,
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
        facet_key: optional facet key whose joins must be applied for computing the facet label.
            Expanded to include ancestor keys (e.g. "subject.species" -> {"subject",
            "subject.species"}). Takes priority over filter/sort joins for the same key.
    """
    facet_keys = set(expand_dotted_key(facet_key)) if facet_key else set()
    if diff := facet_keys.difference(join_specs):
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
        is_facet = name in facet_keys
        if is_facet:
            L.debug("Applying facet join for {!r}", name)
            query = spec.apply_facet_join(query)
        elif is_filter:
            L.debug("Applying filter join for {!r}", name)
            query = spec.apply_filter_join(query)
        elif is_sort:
            L.debug("Applying sort join for {!r}", name)
            query = spec.apply_join(query)
    return query
