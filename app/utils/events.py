def register_model_events() -> None:
    """Register sqlalchemy events."""
    import app.db.events  # ruff:ignore[unused-import, import-outside-top-level]
