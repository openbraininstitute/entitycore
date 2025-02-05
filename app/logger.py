"""Logger configuration."""

import inspect
import json
import logging
import sys
import traceback

import loguru
from loguru import logger

from app.config import settings

L = logger


class InterceptHandler(logging.Handler):
    """Intercept standard logging messages toward Loguru sinks.

    See https://github.com/Delgan/loguru#entirely-compatible-with-standard-logging.
    """

    def emit(self, record: logging.LogRecord) -> None:  # noqa: PLR6301
        """Emit a log record."""
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = L.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        L.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def json_formatter(record: "loguru.Record") -> str:
    """Format a log record including only a subset of fields.

    Return the string to be formatted, not the actual message to be logged.
    See https://loguru.readthedocs.io/en/stable/resources/recipes.html.
    """

    def _format_exception(ex: "loguru.RecordException") -> dict[str, str | None]:
        return {
            "type": ex.type.__name__ if ex.type else None,
            "value": str(ex.value) if ex.value else None,
            "traceback": "".join(traceback.format_exception(ex.type, ex.value, ex.traceback)),
        }

    def _serialize(rec: "loguru.Record") -> str:
        subset = {
            "time": rec["time"].isoformat(),
            "level": rec["level"].name,
            "name": rec["name"],
            "message": rec["message"],
            "extra": rec["extra"],
            "exception": _format_exception(rec["exception"]) if rec["exception"] else None,
        }
        return json.dumps(subset, separators=(",", ":"), default=str)

    record["extra"]["serialized"] = _serialize(record)
    return "{extra[serialized]}\n"


def str_formatter(record: "loguru.Record") -> str:
    """Format a log record including the extra parameters if present.

    Return the string to be formatted, not the actual message to be logged.
    """
    extras = (
        f""" [{"|".join(f"{k}={{extra[{k}]}}" for k in record["extra"])}]"""
        if record["extra"]
        else ""
    )
    return f"{settings.LOG_FORMAT}{extras}\n{{exception}}"


def configure_logging() -> int:
    """Configure logging."""
    L.remove()
    handler_id = L.add(
        sink=sys.stderr,
        level=settings.LOG_LEVEL,
        format=json_formatter if settings.LOG_SERIALIZE else str_formatter,
        backtrace=settings.LOG_BACKTRACE,
        diagnose=settings.LOG_DIAGNOSE,
        enqueue=settings.LOG_ENQUEUE,
        catch=settings.LOG_CATCH,
    )
    L.enable("app")
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.NOTSET, force=True)
    for logger_name, logger_level in settings.LOG_STANDARD_LOGGER.items():
        L.info("Setting standard logger level: {}={}", logger_name, logger_level)
        logging.getLogger(logger_name).setLevel(logger_level)
    L.info("Logging configured")
    return handler_id
