from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_filter.contrib.sqlalchemy.filter import _orm_operator_transformer  # noqa: PLC2701
from pydantic import field_validator
from sqlalchemy import Select, or_
from sqlalchemy.orm import Query


class CustomFilter(Filter):
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

    def filter(self, query: Query | Select, aliases=None):
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
                query = field_value.filter(query, aliases)
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

    @property
    def ordering_values(self):
        values = super().ordering_values

        if not values:
            return []

        all_values = []

        for field_name in values:
            # Nested model ordering values
            field_value = getattr(self, field_name, None)
            if field_name is not None and isinstance(field_value, Filter):
                all_values += field_value.ordering_values
                continue

            # Current model's values

            direction = Filter.Direction.asc
            if field_name.startswith("-"):
                direction = Filter.Direction.desc

            field_name = field_name.replace("-", "").replace("+", "")  # noqa: PLW2901
            field_value = getattr(self.Constants.model, field_name, None)

            if field_value is None:
                msg = f"Invalid ordering field {field_name}"
                raise ValueError(msg)

            all_values.append((field_value, direction))

        return all_values

    def sort(self, query: Query | Select):
        if not self.ordering_values:
            return query

        for field_value, direction in self.ordering_values:
            query = query.order_by(getattr(field_value, direction)())

        return query
