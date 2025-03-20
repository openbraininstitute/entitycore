import uuid

from app.db.model import Agent, ETypeClass, MTypeClass, Species, Strain
from app.filters.base import CustomFilter


class MTypeClassFilter(CustomFilter):
    id: uuid.UUID | None = None
    pref_label: str | None = None
    pref_label__in: list[str] | None = None

    order_by: list[str] = ["pref_label"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = MTypeClass
        ordering_model_fields = ["pref_label"]  # noqa: RUF012


class ETypeClassFilter(CustomFilter):
    id: uuid.UUID | None = None
    pref_label: str | None = None
    pref_label__in: list[str] | None = None

    order_by: list[str] = ["pref_label"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = ETypeClass
        ordering_model_fields = ["pref_label"]  # noqa: RUF012


class SpeciesFilter(CustomFilter):
    id: uuid.UUID | None = None
    name: str | None = None
    name__in: list[str] | None = None

    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Species
        ordering_model_fields = ["name"]  # noqa: RUF012


class StrainFilter(CustomFilter):
    id: uuid.UUID | None = None
    name: str | None = None
    name__in: list[str] | None = None

    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Strain
        ordering_model_fields = ["name"]  # noqa: RUF012


class AgentFilter(CustomFilter):
    id: uuid.UUID | None = None
    pref_label: str | None = None
    pref_label__in: list[str] | None = None

    order_by: list[str] = ["pref_label"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Agent
        ordering_model_fields = ["pref_label"]  # noqa: RUF012
