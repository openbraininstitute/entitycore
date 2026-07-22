"""Logger configuration."""

import json
import logging
import sys
import traceback
import warnings

import loguru
import sqlalchemy.exc
from loguru import logger

from app.config import settings
from app.context import request_context_provider

L = logger


class InterceptHandler(logging.Handler):
    """Intercept standard logging messages toward Loguru sinks.

    Unlike the recipe at
    https://github.com/Delgan/loguru#entirely-compatible-with-standard-logging,
    the caller is read from the LogRecord instead of being re-derived by walking frames,
    so caller attribution keeps working when the handler chain is patched
    (e.g. by Sentry's LoggingIntegration).
    """

    def emit(self, record: logging.LogRecord) -> None:  # ruff:ignore[no-self-use]
        """Emit a log record."""
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = L.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Take the caller from the stdlib record, stamped via findCaller() before any
        # handler runs. Walking frames here would instead pick up whatever patched the
        # handler chain (e.g. Sentry's LoggingIntegration).
        (
            L.patch(
                lambda r: r.update(name=record.name, function=record.funcName, line=record.lineno)
            )
            .opt(exception=record.exc_info)
            .log(level, record.getMessage())
        )


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

    def patcher(record: "loguru.Record") -> None:
        """Add request context (request_id, user_id) to all log records.

        This function is automatically applied to every log message across all modules,
        enriching them with contextual information from the current request.
        """
        ctx = request_context_provider.get({})
        record["extra"].update(ctx)

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
    L.configure(patcher=patcher)
    L.enable("app")
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.NOTSET, force=True)
    for logger_name, logger_level in settings.LOG_STANDARD_LOGGER.items():
        L.info("Setting standard logger level: {}={}", logger_name, logger_level)
        logging.getLogger(logger_name).setLevel(logger_level)
    L.info("Logging configured")
    return handler_id


def configure_warnings():
    """Configure warnings.

    Raise an error in case of potentially wrong queries, for example:
    - SELECT statement has a cartesian product
    - An alias is being generated automatically
    """
    warnings.simplefilter("error", sqlalchemy.exc.SAWarning)
