"""Entity schemas."""

from typing import Annotated
from uuid import UUID

from pydantic import MISSING, RootModel
from sqlalchemy.orm import Load, QueryableAttribute

from app.db.types import DerivationType, EntityLifecycleStatus, EntityType
from app.schemas.asset import AssetsMixin
from app.schemas.base import AuthorizationOptionalPublicMixin, Schema
from app.schemas.expand import Expandable, ExpandableSchema, ExpandLoader, expand_load
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead, NestedIdentifiableRead


class EntityBaseReadMixin:
    authorized_project_id: UUID
    authorized_public: bool
    lifecycle_status: EntityLifecycleStatus


class NestedEntityCreate(Schema):
    """Entity model to be used for bare nested entities in create endpoints."""

    id: UUID


class NestedEntityBareRead(Schema):
    """Minimal nested entity reference with only id and type."""

    id: UUID
    type: EntityType


class NestedEntityRead(NestedIdentifiableRead, EntityBaseReadMixin):
    """Entity model to be used for bare nested entities in read endpoints."""

    type: EntityType


class GeneratedDerivationRead(Schema):
    """A derivation where this entity is the generated (derived) entity."""

    used: NestedEntityRead
    derivation_type: DerivationType
    label: str | None = None


class UsedDerivationRead(Schema):
    """A derivation where this entity is the used (source) entity."""

    generated: NestedEntityRead
    derivation_type: DerivationType
    label: str | None = None


def _derivation_loader(other_side: str) -> ExpandLoader:
    """Return the loader of a derivation list, with the entity on the other side of each one."""

    def load(
        parent: Load | None, attr: QueryableAttribute, qualifiers: frozenset[str] | None
    ) -> list[Load]:
        derivation_class = attr.property.mapper.class_
        if qualifiers is not None:
            derivation_types = [DerivationType(q) for q in qualifiers]
            attr = attr.and_(derivation_class.derivation_type.in_(derivation_types))
        other_entity = getattr(derivation_class, other_side)
        return [expand_load(parent, "selectinload", attr).joinedload(other_entity)]

    return load


class DerivationReadMixin(ExpandableSchema):
    """On-demand derivation lists, available on every entity read (see the `expand` query param).

    A direction that is not expanded is omitted; an expanded direction without derivations is
    ``[]``. The qualifier selects the derivation types, e.g.
    ``expand=generated_from_derivations:circuit_extraction``.
    """

    generated_from_derivations: Annotated[
        list[GeneratedDerivationRead] | MISSING,
        Expandable(
            attr="derivations_as_generated",
            loader=_derivation_loader("used"),
            qualifiers=tuple(DerivationType),
        ),
    ] = MISSING
    used_by_derivations: Annotated[
        list[UsedDerivationRead] | MISSING,
        Expandable(
            attr="derivations_as_used",
            loader=_derivation_loader("generated"),
            qualifiers=tuple(DerivationType),
        ),
    ] = MISSING


from app.schemas.contribution import (  # ruff:ignore[module-import-not-at-top-of-file]
    ContributionReadWithoutEntityMixin,
)


class EntityReadWoutAssets(
    IdentifiableRead,
    EntityBaseReadMixin,
    ContributionReadWithoutEntityMixin,
    DerivationReadMixin,
):
    """Entity model that includes created_by and updated_by information."""

    type: EntityType


class EntityRead(
    IdentifiableRead,
    EntityBaseReadMixin,
    AssetsMixin,
    ContributionReadWithoutEntityMixin,
    DerivationReadMixin,
):
    """Entity model that includes created_by and updated_by information."""

    type: EntityType


class EntityCreate(IdentifiableCreate, AuthorizationOptionalPublicMixin):
    lifecycle_status: EntityLifecycleStatus = EntityLifecycleStatus.active


class EntityCountRead(RootModel[dict[str, int]]):
    """Entity count model that contains the number of entities by type."""


class BasicEntityRead(NestedEntityBareRead):
    """Minimal entity reference for nested relations."""
