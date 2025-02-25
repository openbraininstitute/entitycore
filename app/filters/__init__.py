from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_filter.contrib.sqlalchemy.filter import _orm_operator_transformer  # noqa: PLC2701
from sqlalchemy import or_
from sqlalchemy.orm import Query
from sqlalchemy.sql.selectable import Select

from app.db.model import Agent, Species, Strain


class FilterWithAliases(Filter):
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

    def filter(self, query: Query | Select, aliases=None):
        for field_name, value in self.filtering_fields:
            field_value = getattr(self, field_name)
            if isinstance(field_value, FilterWithAliases):
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


class SpeciesFilter(FilterWithAliases):
    id: int | None = None
    name: str | None = None

    class Constants(FilterWithAliases.Constants):
        model = Species


class StrainFilter(FilterWithAliases):
    id: int | None = None
    name: str | None = None

    class Constants(FilterWithAliases.Constants):
        model = Strain


class AgentFilter(FilterWithAliases):
    id: int | None = None
    pref_label: str | None = None

    class Constants(FilterWithAliases.Constants):
        model = Agent
