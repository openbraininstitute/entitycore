import logging

import pytest
from loguru import logger

from app.logger import InterceptHandler


@pytest.fixture(autouse=True)
def _simulate_sentry_logging_patch(monkeypatch):
    """Wrap Logger.callHandlers with an extra frame, as sentry's LoggingIntegration does.

    Simulates the sentry monkeypatch without initializing the SDK,
    which would patch logging.Logger.callHandlers globally for the whole test session.
    """
    original = logging.Logger.callHandlers

    def patched_call_handlers(self, record):
        return original(self, record)

    monkeypatch.setattr(logging.Logger, "callHandlers", patched_call_handlers)


def _intercept_one_message(logger_name):
    messages = []
    handler_id = logger.add(messages.append, level="INFO")
    handler = InterceptHandler()
    stdlib_logger = logging.getLogger(logger_name)
    stdlib_logger.setLevel(logging.INFO)
    stdlib_logger.propagate = False
    stdlib_logger.addHandler(handler)
    try:
        stdlib_logger.info("intercepted message")
    finally:
        stdlib_logger.removeHandler(handler)
        logger.remove(handler_id)

    assert len(messages) == 1
    return messages[0].record


def test_intercept_handler_reports_caller_module():
    record = _intercept_one_message(__name__)

    assert record["message"] == "intercepted message"
    assert record["name"] == __name__
    assert record["function"] == "_intercept_one_message"


def test_intercept_handler_reports_logger_name():
    record = _intercept_one_message("some.library")

    assert record["message"] == "intercepted message"
    assert record["name"] == "some.library"
