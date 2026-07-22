import logging

import sentry_sdk
from loguru import logger

from app.logger import InterceptHandler


def _intercept_one_message(logger_name):
    sentry_sdk.init(dsn=None)
    assert logging.Logger.callHandlers.__module__ == "sentry_sdk.integrations.logging"

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
