from app.config import settings
from app.db import get_db_sessionmaker

_SESSIONMAKER = None


def get_db():
    """Get a DB session."""
    global _SESSIONMAKER
    if _SESSIONMAKER is None:
        _SESSIONMAKER = get_db_sessionmaker(settings.DB_URI)

    db = _SESSIONMAKER()

    try:
        yield db()
    finally:
        db.close()
