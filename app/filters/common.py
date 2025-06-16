import uuid
from datetime import datetime
from typing import Annotated

from fastapi_filter import FilterDepends, with_prefix

from app.db.model import (
    Agent,
    BrainRegion,
    Contribution,
    Entity,
    ETypeClass,
    MTypeClass,
    Species,
    Strain,
    Subject,
)
from app.filters.base import CustomFilter


class IdFilterMixin:
    id: uuid.UUID | None = None
    id__in: list[uuid.UUID] | None = None


class NameFilterMixin:
    name: str | None = None
    name__in: list[str] | None = None
    name__ilike: str | None = None


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


class AgentFilter(CustomFilter):
    id: uuid.UUID | None = None
    pref_label: str | None = None
    pref_label__in: list[str] | None = None

    order_by: list[str] = ["pref_label"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Agent
        ordering_model_fields = ["pref_label"]  # noqa: RUF012


class CreationFilterMixin:
    creation_date__lte: datetime | None = None
    creation_date__gte: datetime | None = None
    update_date__lte: datetime | None = None
    update_date__gte: datetime | None = None


# Dependencies
MTypeClassFilterDep = Annotated[MTypeClassFilter, FilterDepends(MTypeClassFilter)]
ETypeClassFilterDep = Annotated[ETypeClassFilter, FilterDepends(ETypeClassFilter)]
AgentFilterDep = Annotated[AgentFilter, FilterDepends(AgentFilter)]

# Nested dependencies
NestedMTypeClassFilterDep = FilterDepends(with_prefix("mtype", MTypeClassFilter))
NestedETypeClassFilterDep = FilterDepends(with_prefix("etype", ETypeClassFilter))
NestedContributionFilterDep = FilterDepends(with_prefix("contribution", AgentFilter))
NestedCreatedByFilterDep = FilterDepends(with_prefix("created_by", AgentFilter))
NestedUpdatedByFilterDep = FilterDepends(with_prefix("updated_by", AgentFilter))
NestedAgentFilterDep = FilterDepends(with_prefix("agent", AgentFilter))


class CreatorFilterMixin:
    created_by: Annotated[AgentFilter | None, NestedCreatedByFilterDep] = None
    updated_by: Annotated[AgentFilter | None, NestedUpdatedByFilterDep] = None


class NestedSpeciesFilter(NameFilterMixin, CustomFilter):
    """Species filter with limited fields for nesting."""

    id: uuid.UUID | None = None

    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Species
        ordering_model_fields = ["name"]  # noqa: RUF012


class SpeciesFilter(NestedSpeciesFilter, CreationFilterMixin, CreatorFilterMixin):
    """Full species filter."""


SpeciesFilterDep = Annotated[SpeciesFilter, FilterDepends(SpeciesFilter)]
NestedSpeciesFilterDep = FilterDepends(with_prefix("species", NestedSpeciesFilter))


class NestedStrainFilter(NameFilterMixin, CustomFilter):
    id: uuid.UUID | None = None

    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Strain
        ordering_model_fields = ["name"]  # noqa: RUF012


class StrainFilter(NestedStrainFilter, CreationFilterMixin, CreatorFilterMixin):
    """Full strain filter."""


StrainFilterDep = Annotated[StrainFilter, FilterDepends(StrainFilter)]
NestedStrainFilterDep = FilterDepends(with_prefix("strain", NestedStrainFilter))


class SpeciesFilterMixin:
    species_id__in: list[uuid.UUID] | None = None
    species: Annotated[NestedSpeciesFilter | None, NestedSpeciesFilterDep] = None
    strain: Annotated[NestedStrainFilter | None, NestedStrainFilterDep] = None


class NestedEntityFilter(CustomFilter, IdFilterMixin):
    type: str | None = None
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Entity
        ordering_model_fields = ["-creation_date"]  # noqa: RUF012


NestedEntityFilterDep = FilterDepends(with_prefix("entity", NestedEntityFilter))


class ContributionFilter(CustomFilter, CreationFilterMixin, CreatorFilterMixin):
    id: uuid.UUID | None = None

    agent: Annotated[AgentFilter | None, NestedAgentFilterDep] = None
    entity: Annotated[NestedEntityFilter | None, NestedEntityFilterDep] = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Contribution
        ordering_model_fields = ["-creation_date"]  # noqa: RUF012


ContributionFilterDep = Annotated[ContributionFilter, FilterDepends(ContributionFilter)]


class ContributionFilterMixin:
    contribution: Annotated[AgentFilter | None, NestedContributionFilterDep] = None


class SubjectFilter(ContributionFilterMixin, SpeciesFilterMixin, NameFilterMixin, CustomFilter):
    id: uuid.UUID | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Subject
        ordering_model_fields = ["name"]  # noqa: RUF012


SubjectFilterDep = Annotated[SubjectFilter, FilterDepends(SubjectFilter)]
NestedSubjectFilterDep = FilterDepends(with_prefix("subject", SubjectFilter))


class SubjectFilterMixin:
    subject: Annotated[SubjectFilter | None, NestedSubjectFilterDep] = None


class BrainRegionFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    acronym: str | None = None
    acronym__in: list[str] | None = None
    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = BrainRegion
        ordering_model_fields = ["name"]  # noqa: RUF012


BrainRegionFilterDep = Annotated[BrainRegionFilter, FilterDepends(BrainRegionFilter)]
NestedBrainRegionFilterDep = FilterDepends(with_prefix("brain_region", BrainRegionFilter))


class BrainRegionFilterMixin:
    brain_region: Annotated[BrainRegionFilter | None, NestedBrainRegionFilterDep] = None


class EntityFilterMixin(
    IdFilterMixin,
    CreatorFilterMixin,
    CreationFilterMixin,
    ContributionFilterMixin,
):
    pass


class MTypeClassFilterMixin:
    mtype: Annotated[MTypeClassFilter | None, NestedMTypeClassFilterDep] = None


class ETypeClassFilterMixin:
    etype: Annotated[ETypeClassFilter | None, NestedETypeClassFilterDep] = None
