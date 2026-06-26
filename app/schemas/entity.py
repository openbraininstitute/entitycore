"""Entity schemas."""

from uuid import UUID

from pydantic import RootModel

from app.db.types import EntityLifecycleStatus, EntityType
from app.schemas.asset import AssetsMixin
from app.schemas.base import AuthorizationOptionalPublicMixin, Schema
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


from app.schemas.contribution import ContributionReadWithoutEntityMixin  # noqa: E402


class EntityReadWoutAssets(
    IdentifiableRead,
    EntityBaseReadMixin,
    ContributionReadWithoutEntityMixin,
):
    """Entity model that includes created_by and updated_by information."""

    type: EntityType


class EntityRead(
    IdentifiableRead,
    EntityBaseReadMixin,
    AssetsMixin,
    ContributionReadWithoutEntityMixin,
):
    """Entity model that includes created_by and updated_by information."""

    type: EntityType


class EntityCreate(IdentifiableCreate, AuthorizationOptionalPublicMixin):
    lifecycle_status: EntityLifecycleStatus = EntityLifecycleStatus.active


class EntityCountRead(RootModel[dict[str, int]]):
    """Entity count model that contains the number of entities by type."""


class BasicEntityRead(NestedEntityBareRead):
    """Minimal entity reference for nested relations."""
