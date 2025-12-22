def register_model_events() -> None:
    """Register sqlalchemy events."""
    import app.db.events  # noqa: F401, PLC0415
