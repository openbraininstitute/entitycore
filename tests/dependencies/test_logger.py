from unittest.mock import ANY
from uuid import UUID

from fastapi import Depends

from app.dependencies.logger import logger_context
from app.logger import L

from tests.utils import ADMIN_SUB_ID


def test_logger_context(client_admin):
    """Test that logger_context adds sub_id, request_id, and forwarded_for to logs."""
    logs = []

    def capture_sink(message):
        logs.append(message.record)

    @client_admin.app.get("/test-logger", dependencies=[Depends(logger_context)])
    def test_endpoint():
        L.info("test message")
        return {"ok": True}

    handler_id = L.add(capture_sink, level="INFO")

    try:
        result = client_admin.get("/test-logger", headers={"x-forwarded-for": "127.1.2.3"})

        assert result.status_code == 200
        assert len(logs) == 1

        record = logs[0]
        assert record["message"] == "test message"
        assert record["extra"] == {
            "sub_id": UUID(ADMIN_SUB_ID),
            "request_id": ANY,
            "forwarded_for": "127.1.2.3",
        }
    finally:
        L.remove(handler_id)
