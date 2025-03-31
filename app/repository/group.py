"""Group of repositories."""

from functools import cached_property

from sqlalchemy.orm import Session

from app.repository.asset import AssetRepository
from app.repository.entity import EntityRepository


class RepositoryGroup:
    """Group of repositories sharing the same database session."""

    def __init__(
        self,
        db: Session,
        entity_repo_class: type[EntityRepository] = EntityRepository,
        asset_repo_class: type[AssetRepository] = AssetRepository,
    ) -> None:
        """Init the repository group."""
        self._db = db
        self._entity_repo_class = entity_repo_class
        self._asset_repo_class = asset_repo_class

    @property
    def db(self) -> Session:
        """Return the shared database session."""
        return self._db

    @cached_property
    def entity(self) -> EntityRepository:
        """Return the entity repository."""
        return self._entity_repo_class(self.db)

    @cached_property
    def asset(self) -> AssetRepository:
        """Return the asset repository."""
        return self._asset_repo_class(self.db)
