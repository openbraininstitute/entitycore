"""Entity schemas."""

import uuid

from pydantic import UUID4, RootModel

from app.db.types import EntityLifecycleStatus, EntityType
from app.schemas.asset import AssetsMixin
from app.schemas.base import AuthorizationOptionalPublicMixin, Schema
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead, NestedIdentifiableRead


class EntityBaseMixin:
    authorized_project_id: UUID4
    authorized_public: bool
    lifecycle_status: EntityLifecycleStatus = EntityLifecycleStatus.active


class NestedEntityCreate(Schema):
    """Entity model to be used for bare nested entities in create endpoints."""

    id: uuid.UUID


class NestedEntityBareRead(Schema):
    """Minimal nested entity reference with only id and type."""

    id: uuid.UUID
    type: EntityType


class NestedEntityRead(NestedIdentifiableRead, EntityBaseMixin):
    """Entity model to be used for bare nested entities in read endpoints."""

    type: EntityType


from app.schemas.contribution import ContributionReadWithoutEntityMixin  # noqa: E402


class EntityReadWoutAssets(
    IdentifiableRead,
    EntityBaseMixin,
    ContributionReadWithoutEntityMixin,
):
    """Entity model that includes created_by and updated_by information."""

    type: EntityType


class EntityRead(
    IdentifiableRead,
    EntityBaseMixin,
    AssetsMixin,
    ContributionReadWithoutEntityMixin,
):
    """Entity model that includes created_by and updated_by information."""

    type: EntityType


class EntityCreate(IdentifiableCreate, AuthorizationOptionalPublicMixin):
    pass


class EntityCountRead(RootModel[dict[str, int]]):
    """Entity count model that contains the number of entities by type."""


class BasicEntityRead(NestedEntityBareRead):
    """Minimal entity reference for nested relations."""
