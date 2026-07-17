import uuid
from typing import Annotated

from fastapi_filter import with_prefix

from app.db.model import Derivation, Entity
from app.db.types import DerivationType, EntityLifecycleStatus, EntityType
from app.dependencies.filter import FilterDepends
from app.filters.base import CustomFilter
from app.filters.common import AuthorizedFilterMixin, CreationFilterMixin, IdFilterMixin
from app.filters.person import CreatorFilterMixin


class NestedDerivationFilter(CustomFilter):
    """Filter entities by a related Derivation, on either the generated or used side.

    Exposed on every entity filter as ``generated_derivation`` / ``used_derivation`` (see
    EntityFilterMixin). Besides ``derivation_type``, the related-entity ids are filterable:
    on ``generated_derivation`` the meaningful side is ``used_id`` ("derived from entity X"),
    on ``used_derivation`` it is ``generated_id`` ("source of entity Y").
    """

    derivation_type: DerivationType | None = None
    derivation_type__in: list[DerivationType] | None = None
    used_id: uuid.UUID | None = None
    used_id__in: list[uuid.UUID] | None = None
    generated_id: uuid.UUID | None = None
    generated_id__in: list[uuid.UUID] | None = None

    class Constants(CustomFilter.Constants):
        model = Derivation


class BasicEntityFilter(CustomFilter):
    type: EntityType | None = None

    order_by: list[str] = ["-creation_date"]  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = Entity
        ordering_model_fields = ["creation_date", "update_date", "name"]  # ruff:ignore[mutable-class-default]


BasicEntityFilterDep = Annotated[BasicEntityFilter, FilterDepends(BasicEntityFilter)]


class NestedEntityFilter(CustomFilter, IdFilterMixin):
    type: EntityType | None = None

    class Constants(CustomFilter.Constants):
        model = Entity


NestedEntityFilterDep = FilterDepends(with_prefix("entity", NestedEntityFilter))


# Import after class definitions to avoid circular import
from app.filters.contribution import (  # ruff:ignore[module-import-not-at-top-of-file]
    ContributionFilterMixin,
)


class EntityFilterMixin(
    IdFilterMixin,
    AuthorizedFilterMixin,
    CreatorFilterMixin,
    CreationFilterMixin,
    ContributionFilterMixin,
):
    lifecycle_status: EntityLifecycleStatus | None = None

    # Derivations where this entity is the generated (derived) side: "how it was derived".
    generated_derivation: Annotated[
        NestedDerivationFilter | None,
        FilterDepends(with_prefix("generated_derivation", NestedDerivationFilter)),
    ] = None
    # Derivations where this entity is the used (source) side: "what was derived from it".
    used_derivation: Annotated[
        NestedDerivationFilter | None,
        FilterDepends(with_prefix("used_derivation", NestedDerivationFilter)),
    ] = None
