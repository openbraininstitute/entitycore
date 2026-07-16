import sentry_sdk

from app import sentry as test_module
from app.config import settings


def test_init_sentry():
    test_module.init_sentry()

    client = sentry_sdk.get_client()
    assert client.is_active()
    assert client.transport is None  # without a DSN nothing is sent
    assert client.options["environment"] == settings.DEPLOYMENT_ENV
    assert client.options["release"] == settings.APP_VERSION
    assert client.options["traces_sample_rate"] == settings.SENTRY_TRACES_SAMPLE_RATE
    assert (
        client.options["profile_session_sample_rate"] == settings.SENTRY_PROFILE_SESSION_SAMPLE_RATE
    )
    assert client.options["profile_lifecycle"] == "trace"
