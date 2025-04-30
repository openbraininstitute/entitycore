import uuid
from datetime import datetime
from typing import Annotated

from fastapi_filter import FilterDepends, with_prefix

from app.db.model import Agent, ETypeClass, MTypeClass, Species, Strain, Subject, SynapticPathway
from app.filters.base import CustomFilter


class NameFilterMixin:
    name: str | None = None
    name__in: list[str] | None = None


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


class SpeciesFilter(NameFilterMixin, CustomFilter):
    id: uuid.UUID | None = None

    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Species
        ordering_model_fields = ["name"]  # noqa: RUF012


class StrainFilter(NameFilterMixin, CustomFilter):
    id: uuid.UUID | None = None

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


class CreationFilterMixin:
    creation_date__lte: datetime | None = None
    creation_date__gte: datetime | None = None
    update_date__lte: datetime | None = None
    update_date__gte: datetime | None = None


# Dependencies
MTypeClassFilterDep = Annotated[MTypeClassFilter, FilterDepends(MTypeClassFilter)]
ETypeClassFilterDep = Annotated[ETypeClassFilter, FilterDepends(ETypeClassFilter)]
SpeciesFilterDep = Annotated[SpeciesFilter, FilterDepends(SpeciesFilter)]
StrainFilterDep = Annotated[StrainFilter, FilterDepends(StrainFilter)]
AgentFilterDep = Annotated[AgentFilter, FilterDepends(AgentFilter)]

# Nested dependencies
NestedMTypeClassFilterDep = FilterDepends(with_prefix("mtype", MTypeClassFilter))
NestedETypeClassFilterDep = FilterDepends(with_prefix("etype", ETypeClassFilter))
NestedSpeciesFilterDep = FilterDepends(with_prefix("species", SpeciesFilter))
NestedStrainFilterDep = FilterDepends(with_prefix("strain", StrainFilter))
NestedAgentFilterDep = FilterDepends(with_prefix("contribution", AgentFilter))


class CreatorFilterMixin:
    createdBy: Annotated[AgentFilter | None, NestedAgentFilterDep] = None
    updatedBy: Annotated[AgentFilter | None, NestedAgentFilterDep] = None


class SpeciesFilterMixin:
    species_id_in: list[int] | None = None
    species: Annotated[SpeciesFilter | None, NestedSpeciesFilterDep] = None


class StrainFilterMixin:
    strain: Annotated[StrainFilter | None, NestedStrainFilterDep] = None


class ContributionFilterMixin:
    contribution: Annotated[AgentFilter | None, NestedAgentFilterDep] = None


class SubjectFilter(ContributionFilterMixin, SpeciesFilterMixin, NameFilterMixin, CustomFilter):
    id: uuid.UUID | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Subject
        ordering_model_fields = ["name"]  # noqa: RUF012


SubjectFilterDep = Annotated[SubjectFilter, FilterDepends(SubjectFilter)]
NestedSubjectFilterDep = FilterDepends(with_prefix("subject", SubjectFilter))


class BrainRegionFilterMixin:
    brain_region_id: int | None = None


class MTypeClassFilterMixin:
    mtype: Annotated[MTypeClassFilter | None, NestedMTypeClassFilterDep] = None


class ETypeClassFilterMixin:
    etype: Annotated[ETypeClassFilter | None, NestedETypeClassFilterDep] = None


class SynapticPathwayFilter(CustomFilter):
    pre_mtype: Annotated[MTypeClassFilter | None, NestedMTypeClassFilterDep] = None
    post_mtype: Annotated[MTypeClassFilter | None, NestedMTypeClassFilterDep] = None
    pre_region: int | None = None
    post_region: int | None = None

    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = SynapticPathway
        ordering_model_fields = ["name"]  # noqa: RUF012


SynapticPathwayFilterDep = Annotated[SynapticPathwayFilter, FilterDepends(SynapticPathwayFilter)]
NestedSynapticPathwayFilterDep = FilterDepends(
    with_prefix("synaptic_pathway", SynapticPathwayFilter)
)


class SynapticPathwayFilterMixin:
    synaptic_pathway: Annotated[SynapticPathwayFilter | None, NestedSynapticPathwayFilterDep] = None
