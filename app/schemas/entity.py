"""Entity schemas."""

from uuid import UUID

from pydantic import RootModel

from app.db.types import DerivationType, EntityLifecycleStatus, EntityType
from app.schemas.asset import AssetsMixin
from app.schemas.base import AuthorizationOptionalPublicMixin, Schema
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead, NestedIdentifiableRead


class EntityBaseMixin:
    authorized_project_id: UUID
    authorized_public: bool
    lifecycle_status: EntityLifecycleStatus = EntityLifecycleStatus.active


class NestedEntityCreate(Schema):
    """Entity model to be used for bare nested entities in create endpoints."""

    id: UUID


class NestedEntityBareRead(Schema):
    """Minimal nested entity reference with only id and type."""

    id: UUID
    type: EntityType


class NestedEntityRead(NestedIdentifiableRead, EntityBaseMixin):
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


class DerivationReadMixin:
    """On-demand derivation lists, available on every entity read (see the `expand` query param).

    A direction that was not expanded serializes as ``null`` (load-aware property on the Entity
    model, so no extra query and `raiseload` is never tripped); an expanded-but-empty direction
    serializes as ``[]``.
    """

    generated_from_derivations: list[GeneratedDerivationRead] | None = None
    used_by_derivations: list[UsedDerivationRead] | None = None


from app.schemas.contribution import ContributionReadWithoutEntityMixin  # noqa: E402


class EntityReadWoutAssets(
    IdentifiableRead,
    EntityBaseMixin,
    ContributionReadWithoutEntityMixin,
    DerivationReadMixin,
):
    """Entity model that includes created_by and updated_by information."""

    type: EntityType


class EntityRead(
    IdentifiableRead,
    EntityBaseMixin,
    AssetsMixin,
    ContributionReadWithoutEntityMixin,
    DerivationReadMixin,
):
    """Entity model that includes created_by and updated_by information."""

    type: EntityType


class EntityCreate(IdentifiableCreate, AuthorizationOptionalPublicMixin):
    pass


class EntityCountRead(RootModel[dict[str, int]]):
    """Entity count model that contains the number of entities by type."""


class BasicEntityRead(NestedEntityBareRead):
    """Minimal entity reference for nested relations."""
