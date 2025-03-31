"""Base repository module."""

from sqlalchemy.orm import Session


class BaseRepository:
    """BaseRepository."""

    def __init__(self, db: Session) -> None:
        """Init the repository."""
        self.db = db
