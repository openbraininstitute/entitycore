from app.db.model import Agent, MTypeClass, Species, Strain
from app.filters.base import CustomFilter


class MTypeClassFilter(CustomFilter):
    id: int | None = None
    pref_label: str | None = None
    pref_label__in: list[str] | None = None

    order_by: list[str] = ["pref_label"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = MTypeClass
        ordering_model_fields = ["id", "pref_label"]  # noqa: RUF012


class SpeciesFilter(CustomFilter):
    id: int | None = None
    name: str | None = None
    name__in: list[str] | None = None

    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Species
        ordering_model_fields = ["id", "name"]  # noqa: RUF012


class StrainFilter(CustomFilter):
    id: int | None = None
    name: str | None = None
    name__in: list[str] | None = None

    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Strain
        ordering_model_fields = ["id", "name"]  # noqa: RUF012


class AgentFilter(CustomFilter):
    id: int | None = None
    pref_label: str | None = None
    pref_label__in: list[str] | None = None

    order_by: list[str] = ["pref_label"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Agent
        ordering_model_fields = ["id", "pref_label"]  # noqa: RUF012
