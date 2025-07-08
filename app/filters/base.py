from collections import defaultdict
from operator import attrgetter
from typing import cast

from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_filter.contrib.sqlalchemy.filter import _orm_operator_transformer  # noqa: PLC2701
from pydantic import field_validator
from sqlalchemy import Select, or_
from sqlalchemy.orm import DeclarativeBase

from app.db.model import Identifiable
from app.logger import L

Aliases = dict[type[Identifiable], type[Identifiable] | dict[str, type[Identifiable]]]


class CustomFilter[T: DeclarativeBase](Filter):
    """Custom common filter."""

    class Constants(Filter.Constants):
        ordering_model_fields: list[str]

    @field_validator("*", mode="before")
    @classmethod
    def split_str(cls, value, field):  # pyright: ignore reportIncompatibleMethodOverride
        """Prevent splitting field logic from parent class."""
        # backwards compatibility by splitting only comma separated single list elements that do not
        # have space directly after the comma. e.g "a,b,c" will be split but not 'a, b, c'.
        if (
            field.field_name is not None  # noqa: PLR0916
            and (
                field.field_name == cls.Constants.ordering_field_name
                or field.field_name.endswith("__in")
                or field.field_name.endswith("__not_in")
            )
            and value
            and len(value) == 1
            and isinstance(value[0], str)
            and "," in value[0]
            and ", " not in value[0]
        ):
            msg = (
                "Deprecated comma separated single-string IN query used instead of native list. "
                f"Filter: field.config['title'] Field name: {field.field_name} Value: {value}"
            )
            L.warning(msg)
            return value[0].split(",")
        return value

    @field_validator("order_by", check_fields=False)
    @classmethod
    def restrict_sortable_fields(cls, value: list[str]):
        """Restrict sorting to specific fields."""
        allowed_field_names = getattr(cls.Constants, "ordering_model_fields", None)
        if not allowed_field_names:
            msg = "You cannot sort by any field"
            raise ValueError(msg)

        for name in value:
            field_name = name.replace("+", "").replace("-", "")
            if field_name not in allowed_field_names:
                msg = f"You may only sort by: {', '.join(allowed_field_names)}"
                raise ValueError(msg)

        return value

    @field_validator("*", mode="before", check_fields=False)
    @classmethod
    def validate_order_by(cls, value, field):  # pyright: ignore reportIncompatibleMethodOverride
        return value
        if field.field_name != cls.Constants.ordering_field_name:
            return value

        if not value:
            return None

        field_name_usages = defaultdict(list)
        duplicated_field_names = set()

        for field_name_with_direction in value:
            field_name = field_name_with_direction.replace("-", "").replace("+", "")

            if not (hasattr(cls.Constants.model, field_name) and "__" not in field_name):
                msg = f"{field_name} is not a valid ordering field."
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

    def filter[T: DeclarativeBase](self, query: Select[tuple[T]], aliases: Aliases | None = None):  # type:ignore[override]
        """Allow passing aliases to the filter.

        Due to the complications of handling the inheritance between models, sometimes an alias is
        needed.  Currently only a single alias is supported per model, by passing an `aliases`.

        Ex:
            agent_alias = aliased(Agent, flat=True)
            query = (....
                .outerjoin(agent_alias, Contribution.agent_id == agent_alias.id)
                )
            query = morphology_filter.filter(query, aliases={Agent: agent_alias})
        """
        for field_name, value in self.filtering_fields:
            field_value = getattr(self, field_name)
            if isinstance(field_value, CustomFilter):
                # Allow specifying for a model the alias to map the field_name to
                # {"MTypeClass": {"pre_mtype": alias1, "post_mtype": alias2}}
                new_aliases: Aliases | None = aliases
                if (
                    aliases
                    and (alias := aliases.get(field_value.Constants.model))
                    and isinstance(alias, dict)
                ):
                    if alias_value := alias.get(field_name):
                        new_aliases = {field_value.Constants.model: alias_value}
                    else:
                        # There is no alias for this particular field_name, use model as normal
                        new_aliases = None

                query = field_value.filter(query, new_aliases)
            else:
                if "__" in field_name:
                    # PLW2901 `for` loop variable `field_name` overwritten by assignment target
                    field_name, operator = field_name.split("__")  # noqa: PLW2901
                    operator, value = _orm_operator_transformer[operator](value)  # noqa: PLW2901
                else:
                    operator = "__eq__"

                if field_name == self.Constants.search_field_name and hasattr(
                    self.Constants, "search_model_fields"
                ):
                    search_filters = [
                        getattr(self.Constants.model, field).ilike(f"%{value}%")
                        for field in self.Constants.search_model_fields
                    ]
                    query = query.filter(or_(*search_filters))
                else:
                    # { CODE is different from fastapi_filter here
                    if aliases and self.Constants.model in aliases:
                        alias = aliases[self.Constants.model]
                        model_field = getattr(alias, field_name)
                    else:  # }
                        model_field = getattr(self.Constants.model, field_name)

                    query = query.filter(getattr(model_field, operator)(value))
        return query

    def sort(self, query: Select[tuple[T]], aliases):  # type:ignore[override]
        if not self.ordering_values:
            return query

        for direction, field_name in self.separate_ordering_direction_value():
            model = self.Constants.model

            if "__" in field_name:
                submodel_name, *parts, field_name = field_name.split("__")  # noqa: PLW2901

                rel = getattr(model, submodel_name)
                model = rel.property.mapper.class_

                if model in aliases:
                    model = aliases[model]

                for part in parts:
                    rel = getattr(model, part)
                    model = rel.property.mapper.class_

            order_by_field = getattr(model, field_name)

            query = query.order_by(getattr(order_by_field, direction)())

        return cast("Select[tuple[T]]", query)

    def separate_ordering_direction_value(self) -> list[tuple[Filter.Direction, str]]:
        return [
            (
                Filter.Direction.desc if field_name.startswith("-") else Filter.Direction.asc,
                field_name.replace("-", "").replace("+", ""),
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
    def nested_ordering_fields(self):
        """Return nested ordering fields."""
        return [
            field_name
            for _, field_name in self.separate_ordering_direction_value()
            if "__" in field_name
        ]
