"""Group of repositories."""

from functools import cached_property

from sqlalchemy.orm import Session

from app.repository.asset import AssetRepository


class RepositoryGroup:
    """Group of repositories sharing the same database session."""

    def __init__(
        self,
        db: Session,
        asset_repo_class: type[AssetRepository] = AssetRepository,
    ) -> None:
        """Init the repository group."""
        self._db = db
        self._asset_repo_class = asset_repo_class

    @property
    def db(self) -> Session:
        """Return the shared database session."""
        return self._db

    @cached_property
    def asset(self) -> AssetRepository:
        """Return the asset repository."""
        return self._asset_repo_class(self.db)
