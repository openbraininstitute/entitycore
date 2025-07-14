import uuid
from datetime import datetime
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import (
    Agent,
    BrainRegion,
    Contribution,
    Entity,
    ETypeClass,
    MTypeClass,
    Species,
    Strain,
)
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter


class IdFilterMixin:
    id: uuid.UUID | None = None

    # id__in needs to be a str for backwards compatibility when instead of a native list a comma
    # separated string is provided, e.g. 'id1,id2' . With list[UUID] backwards compatibility would
    # fail because of validation of the field which would be expected to be a UUID.
    id__in: list[str] | None = None


class NameFilterMixin:
    name: str | None = None
    name__in: list[str] | None = None
    name__ilike: str | None = None


class PrefLabelMixin:
    pref_label: str | None = None
    pref_label__in: list[str] | None = None


class NestedMTypeClassFilter(IdFilterMixin, PrefLabelMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = MTypeClass


class MTypeClassFilter(NestedMTypeClassFilter):
    order_by: list[str] = ["pref_label"]  # noqa: RUF012

    class Constants(NestedMTypeClassFilter.Constants):
        ordering_model_fields = ["pref_label"]  # noqa: RUF012


class NestedETypeClassFilter(IdFilterMixin, PrefLabelMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = ETypeClass


class ETypeClassFilter(NestedETypeClassFilter):
    order_by: list[str] = ["pref_label"]  # noqa: RUF012

    class Constants(NestedETypeClassFilter.Constants):
        ordering_model_fields = ["pref_label"]  # noqa: RUF012


class NestedAgentFilter(IdFilterMixin, PrefLabelMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = Agent


class AgentFilter(NestedAgentFilter):
    order_by: list[str] = ["pref_label"]  # noqa: RUF012

    class Constants(NestedAgentFilter.Constants):
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
NestedMTypeClassFilterDep = FilterDepends(with_prefix("mtype", NestedMTypeClassFilter))
NestedETypeClassFilterDep = FilterDepends(with_prefix("etype", NestedETypeClassFilter))
NestedContributionFilterDep = FilterDepends(with_prefix("contribution", NestedAgentFilter))
NestedCreatedByFilterDep = FilterDepends(with_prefix("created_by", NestedAgentFilter))
NestedUpdatedByFilterDep = FilterDepends(with_prefix("updated_by", NestedAgentFilter))
NestedAgentFilterDep = FilterDepends(with_prefix("agent", NestedAgentFilter))


class CreatorFilterMixin:
    created_by: Annotated[NestedAgentFilter | None, NestedCreatedByFilterDep] = None
    updated_by: Annotated[NestedAgentFilter | None, NestedUpdatedByFilterDep] = None


class NestedSpeciesFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    """Species filter with limited fields for nesting."""

    class Constants(CustomFilter.Constants):
        model = Species


class SpeciesFilter(CreationFilterMixin, CreatorFilterMixin, NestedSpeciesFilter):
    """Full species filter."""

    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(NestedSpeciesFilter.Constants):
        ordering_model_fields = ["name"]  # noqa: RUF012


SpeciesFilterDep = Annotated[SpeciesFilter, FilterDepends(SpeciesFilter)]
NestedSpeciesFilterDep = FilterDepends(with_prefix("species", NestedSpeciesFilter))


class NestedStrainFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    class Constants(CustomFilter.Constants):
        model = Strain


class StrainFilter(CreationFilterMixin, CreatorFilterMixin, NestedStrainFilter):
    """Full strain filter."""

    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(NestedStrainFilter.Constants):
        ordering_model_fields = ["name"]  # noqa: RUF012


StrainFilterDep = Annotated[StrainFilter, FilterDepends(StrainFilter)]
NestedStrainFilterDep = FilterDepends(with_prefix("strain", NestedStrainFilter))


class SpeciesFilterMixin:
    species_id__in: list[uuid.UUID] | None = None
    species: Annotated[NestedSpeciesFilter | None, NestedSpeciesFilterDep] = None
    strain: Annotated[NestedStrainFilter | None, NestedStrainFilterDep] = None


class NestedEntityFilter(CustomFilter, IdFilterMixin):
    type: str | None = None

    class Constants(CustomFilter.Constants):
        model = Entity


NestedEntityFilterDep = FilterDepends(with_prefix("entity", NestedEntityFilter))


class NestedContributionFilter(IdFilterMixin, CreationFilterMixin, CustomFilter):
    agent: Annotated[
        NestedAgentFilter | None,
        FilterDepends(with_prefix("contribution__agent", NestedAgentFilter)),
    ] = None
    entity: Annotated[
        NestedEntityFilter | None,
        FilterDepends(with_prefix("contribution__entity", NestedEntityFilter)),
    ] = None

    class Constants(CustomFilter.Constants):
        model = Contribution


class ContributionFilter(IdFilterMixin, CreationFilterMixin, CreatorFilterMixin, CustomFilter):
    agent: Annotated[NestedAgentFilter | None, NestedAgentFilterDep] = None
    entity: Annotated[NestedEntityFilter | None, NestedEntityFilterDep] = None
    order_by: list[str] = ["-creation_date"]  # noqa: RUF012

    class Constants(CustomFilter.Constants):
        model = Contribution
        ordering_model_fields = ["creation_date"]  # noqa: RUF012


ContributionFilterDep = Annotated[ContributionFilter, FilterDepends(ContributionFilter)]


class ContributionFilterMixin:
    contribution: Annotated[NestedAgentFilter | None, NestedContributionFilterDep] = None


class NestedBrainRegionFilter(IdFilterMixin, NameFilterMixin, CustomFilter):
    acronym: str | None = None
    acronym__in: list[str] | None = None

    class Constants(CustomFilter.Constants):
        model = BrainRegion


class BrainRegionFilter(CreationFilterMixin, CreatorFilterMixin, NestedBrainRegionFilter):
    order_by: list[str] = ["name"]  # noqa: RUF012

    class Constants(NestedBrainRegionFilter.Constants):
        ordering_model_fields = ["name"]  # noqa: RUF012


BrainRegionFilterDep = Annotated[BrainRegionFilter, FilterDepends(BrainRegionFilter)]
NestedBrainRegionFilterDep = FilterDepends(with_prefix("brain_region", NestedBrainRegionFilter))


class BrainRegionFilterMixin:
    brain_region: Annotated[NestedBrainRegionFilter | None, NestedBrainRegionFilterDep] = None


class EntityFilterMixin(
    IdFilterMixin,
    CreatorFilterMixin,
    CreationFilterMixin,
    ContributionFilterMixin,
):
    pass


class MTypeClassFilterMixin:
    mtype: Annotated[NestedMTypeClassFilter | None, NestedMTypeClassFilterDep] = None


class ETypeClassFilterMixin:
    etype: Annotated[NestedETypeClassFilter | None, NestedETypeClassFilterDep] = None
