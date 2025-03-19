import uuid


def create_uuid() -> uuid.UUID:
    """Return a new random UUIDv4."""
    return uuid.uuid4()
