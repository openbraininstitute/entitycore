import logging

import sentry_sdk
from loguru import logger

from app.logger import InterceptHandler


def test_intercept_handler_reports_caller_module():
    sentry_sdk.init(dsn=None)
    assert logging.Logger.callHandlers.__module__ == "sentry_sdk.integrations.logging"

    messages = []
    handler_id = logger.add(messages.append, level="INFO")
    handler = InterceptHandler()
    stdlib_logger = logging.getLogger("test_intercept_handler")
    stdlib_logger.setLevel(logging.INFO)
    stdlib_logger.propagate = False
    stdlib_logger.addHandler(handler)
    try:
        stdlib_logger.info("intercepted message")
    finally:
        stdlib_logger.removeHandler(handler)
        logger.remove(handler_id)

    assert len(messages) == 1
    record = messages[0].record
    assert record["message"] == "intercepted message"
    assert record["name"] == __name__
    assert record["function"] == "test_intercept_handler_reports_caller_module"
