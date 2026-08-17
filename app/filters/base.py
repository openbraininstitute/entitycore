from collections import defaultdict
from operator import attrgetter
from typing import cast

from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_filter.contrib.sqlalchemy.filter import (
    _orm_operator_transformer,  # ruff:ignore[import-private-name]
)
from pydantic import field_validator
from sqlalchemy import Select, or_
from sqlalchemy.orm import DeclarativeBase

from app.utils.pattern import convert_to_ilike_pattern

type Aliases[T: DeclarativeBase] = dict[type[T], dict[str, type[T]]]


NESTED_SEPARATOR = "__"
ILIKE_SEARCH_FIELDS = ["name", "description"]
ILIKE_SEARCH_FIELD_NAME = "ilike_search"


class CustomFilter[T: DeclarativeBase](Filter):
    """Custom common filter."""

    class Constants(Filter.Constants):
        ordering_model_fields: list[str]

    @field_validator("*", mode="before")
    @classmethod
    def split_str(cls, value, field):  # pyright: ignore reportIncompatibleMethodOverride  # ruff:ignore[unused-class-method-argument]
        """Prevent splitting field logic from parent class."""
        return value

    @field_validator("order_by", check_fields=False)
    @classmethod
    def restrict_sortable_fields(cls, value: list[str]):
        """Restrict sorting to fields in Constants.ordering_model_fields, stripping +/- prefix."""
        allowed_field_names = getattr(cls.Constants, "ordering_model_fields", None)
        if not allowed_field_names:
            msg = "You cannot sort by any field"
            raise ValueError(msg)

        for name in value:
            field_name = name.lstrip("+-")
            if field_name not in allowed_field_names:
                msg = f"You may only sort by: {', '.join(allowed_field_names)}"
                raise ValueError(msg)

        return value

    @field_validator("*", mode="before", check_fields=False)
    @classmethod
    def validate_order_by(cls, value, field):  # pyright: ignore reportIncompatibleMethodOverride
        """Override parent method to allow fields with __."""
        if field.field_name != cls.Constants.ordering_field_name:
            return value

        if not value:
            return None

        field_name_usages = defaultdict(list)
        duplicated_field_names = set()

        for field_name_with_direction in value:
            field_name = field_name_with_direction.lstrip("+-")

            # different than parent: fields with __ are skipped
            if NESTED_SEPARATOR not in field_name and not hasattr(cls.Constants.model, field_name):
                msg = f"{field_name} is not a valid ordering field."
                raise ValueError(msg)

            # different than parent: a check for prepending space in field name is added
            if field_name.startswith(" "):
                msg = (
                    f"Prepending space found in {field_name}. Please make sure that '+' is encoded "
                    "properly and is not converted into space."
                )
                raise ValueError(msg)

            field_name_usages[field_name].append(field_name_with_direction)
            if len(field_name_usages[field_name]) > 1:
                duplicated_field_names.add(field_name)

        if duplicated_field_names:
            ambiguous_field_names = ", ".join(
                [
                    field_name_with_direction
                    for field_name in sorted(duplicated_field_names)
                    for field_name_with_direction in field_name_usages[field_name]
                ]
            )
            msg = (
                f"Field names can appear at most once for {cls.Constants.ordering_field_name}. "
                f"The following was ambiguous: {ambiguous_field_names}."
            )
            raise ValueError(msg)

        return value

    def filter[T: DeclarativeBase](  # type:ignore[override]
        self,
        query: Select[tuple[T]],
        aliases: Aliases | None = None,
        *,
        _ancestors: tuple[str, ...] = (),
    ) -> Select[tuple[T]]:
        """Apply filtering, resolving aliases by dot-qualified path.

        Args:
            query: The select query to filter.
            aliases: Dict of {ModelClass: {name: alias}} for alias resolution.
            _ancestors: Ancestor filter names leading to this node in the filter hierarchy.
        """
        model = self.Constants.model
        if _ancestors and aliases and (alias_dict := aliases.get(model)):
            model = alias_dict[".".join(_ancestors)]

        for field_name, value in self.filtering_fields:
            field_value = getattr(self, field_name)
            if isinstance(field_value, CustomFilter):
                query = field_value.filter(query, aliases, _ancestors=(*_ancestors, field_name))
            else:
                if "__" in field_name:
                    field_name, operator = field_name.split(NESTED_SEPARATOR)  # ruff:ignore[redefined-loop-name]
                    operator, value = _orm_operator_transformer[operator](value)  # ruff:ignore[redefined-loop-name]
                else:
                    operator = "__eq__"

                if field_name == self.Constants.search_field_name and hasattr(
                    self.Constants, "search_model_fields"
                ):
                    pattern = convert_to_ilike_pattern(value)
                    search_filters = [
                        getattr(model, field).ilike(pattern, escape="\\")
                        for field in self.Constants.search_model_fields
                    ]
                    query = query.filter(or_(*search_filters))
                else:
                    model_field = getattr(model, field_name)
                    query = query.filter(getattr(model_field, operator)(value))
        return query

    def sort(self, query: Select[tuple[T]], aliases: Aliases | None = None) -> Select[tuple[T]]:  # type:ignore[override]
        """Sort query taking into account nested fields and aliases.

        Nested ordering fields (e.g. "me_model__etype__pref_label") are split into
        [*parts, field_name]. Each part must correspond to a nested CustomFilter field
        on the previous filter (starting from self), so that ordering and filtering use
        the same names even when the filter name differs from the DB relationship name
        (e.g. filter "etype" vs relationship "etypes").

        Aliases are resolved using the accumulated dot-path (e.g. "synaptome.me_model").

        Ordering value examples:
            - creation_date
            - subject__species__name
            - me_model__etype__pref_label
        """
        if aliases is None:
            aliases = {}

        if not self.ordering_values:
            return query

        for direction, field_name in self._separate_ordering_direction_value():
            model = self.Constants.model

            if NESTED_SEPARATOR in field_name:
                original_field_name = field_name
                *parts, field_name = field_name.split(NESTED_SEPARATOR)  # ruff:ignore[redefined-loop-name]
                nested_filter = self
                path_parts: list[str] = []

                for part in parts:
                    nested_filter = getattr(nested_filter, part, None)
                    if not isinstance(nested_filter, CustomFilter):
                        msg = f"Unsupported ordering part {part!r} in {original_field_name!r}"
                        raise ValueError(msg)  # ruff:ignore[type-check-without-type-error]
                    model = nested_filter.Constants.model
                    path_parts.append(part)

                    if alias_dict := aliases.get(model):
                        qualified_key = ".".join(path_parts)
                        model = alias_dict[qualified_key]

            order_by_field = getattr(model, field_name)

            query = query.order_by(getattr(order_by_field, direction)())

        return cast("Select[tuple[T]]", query)

    def _separate_ordering_direction_value(self) -> list[tuple[Filter.Direction, str]]:
        """Return list of (direction, field_name) ordering fields."""
        return [
            (
                Filter.Direction.desc if field_name.startswith("-") else Filter.Direction.asc,
                field_name.lstrip("+-"),
            )
            for field_name in self.ordering_values
        ]

    def has_filtering_fields(self) -> bool:
        """Return True if any filtering field is not None, considering also nested filters."""
        for field_name, _value in self.filtering_fields:
            field_value = getattr(self, field_name)
            if not isinstance(field_value, CustomFilter):
                return True
            if field_value.has_filtering_fields():
                return True
        return False

    def has_nested_filtering_field(self, name: str) -> bool:
        """Return True if the specified nested field is not None.

        Args:
            name: The name of the nested filtering field. It's possible to specify deeply nested
            filtering fields using the dot notation, e.g. "measurement_kind.pref_label".
        """
        attr = attrgetter(name)(self)
        # ignore nested filters because they are not valid fields
        return not isinstance(attr, CustomFilter) and attr is not None

    def get_nested_filter(self, name: str) -> "CustomFilter[T] | None":
        """Return the nested filter if it has filtering fields, or None otherwise.

        Args:
            name: The name of the nested filter. It's possible to specify deeply nested filters
            using the dot notation, e.g. "measurement_annotation.measurement_kind".
        """
        attr = attrgetter(name)(self)
        if isinstance(attr, CustomFilter) and attr.has_filtering_fields():
            return attr
        return None

    @property
    def nested_ordering_fields(self) -> list[str]:
        """Nested ordering fields."""
        return [
            field_name
            for _, field_name in self._separate_ordering_direction_value()
            if NESTED_SEPARATOR in field_name
        ]
