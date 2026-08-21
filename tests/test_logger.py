import logging

import pytest
from loguru import logger

from app import logger as test_module


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
    handler = test_module.InterceptHandler()
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


@pytest.fixture
def capture_logged_messages():
    messages = []
    handler_id = logger.add(messages.append, level="INFO")
    yield messages
    logger.remove(handler_id)


def test_timed_success(capture_logged_messages):
    with test_module.timed("operation"):
        pass

    assert len(capture_logged_messages) == 2
    assert capture_logged_messages[0].record["message"] == "operation..."
    final = capture_logged_messages[1].record["message"]
    assert final.startswith("operation... done in ")
    assert final.endswith("ms")


def test_timed_failure(capture_logged_messages):
    err_msg = "boom"
    with (
        pytest.raises(ValueError, match=err_msg),
        test_module.timed("operation"),
    ):
        raise ValueError(err_msg)

    assert len(capture_logged_messages) == 2
    assert capture_logged_messages[0].record["message"] == "operation..."
    final = capture_logged_messages[1].record["message"]
    assert final.startswith("operation... failed in ")
    assert final.endswith("ms")


def test_timed_custom_level(capture_logged_messages):
    with test_module.timed("operation", level="WARNING"):
        pass

    assert all(m.record["level"].name == "WARNING" for m in capture_logged_messages)
