from operator import attrgetter
from typing import cast

from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_filter.contrib.sqlalchemy.filter import _orm_operator_transformer  # noqa: PLC2701
from pydantic import field_validator
from sqlalchemy import Select, or_
from sqlalchemy.orm import DeclarativeBase

from app.db.model import Identifiable

Aliases = dict[type[Identifiable], type[Identifiable] | dict[str, type[Identifiable]]]


class CustomFilter[T: DeclarativeBase](Filter):
    """Custom common filter."""

    class Constants(Filter.Constants):
        ordering_model_fields: list[str]

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

    def sort(self, query: Select[tuple[T]]):  # type:ignore[override]
        return cast("Select[tuple[T]]", super().sort(query))

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
