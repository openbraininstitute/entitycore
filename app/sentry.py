"""Sentry integration."""

import sentry_sdk

from app.config import settings


def init_sentry() -> None:
    """Initialize the Sentry SDK.

    Must be called after ``configure_logging``, which removes all the loguru handlers,
    including the ones registered by the Sentry loguru integration.
    """
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.DEPLOYMENT_ENV,
        release=settings.APP_VERSION,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profile_session_sample_rate=settings.SENTRY_PROFILE_SESSION_SAMPLE_RATE,
        profile_lifecycle="trace",
    )
