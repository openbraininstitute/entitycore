from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    NameDescriptionMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin


class CellCompositionRead(
    CreationMixin,
    AuthorizationMixin,
    IdentifiableMixin,
    EntityTypeMixin,
    ContributionReadWithoutEntityMixin,
    AssetsMixin,
    NameDescriptionMixin,
):
    pass
