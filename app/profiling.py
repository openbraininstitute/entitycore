"""SQL query profiling via SQLAlchemy events.

Enable by setting the environment variable: PROFILING_ENABLED=1

Logs each SQL query with execution time, and summarizes per-request totals.

The query log is stored in a ContextVar holding a mutable list. The middleware sets the list
before dispatching the request; the worker thread (sync route handler) inherits the same list
reference via context copy and appends to it. After the response, the middleware reads the
populated list from the same reference.
"""

import time
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Connection, Engine
from starlette.requests import Request

from app.config import settings
from app.logger import L

_query_log_var: ContextVar[list[dict[str, Any]]] = ContextVar("query_log")


def _get_query_log() -> list[dict[str, Any]]:
    try:
        return _query_log_var.get()
    except LookupError:
        log: list[dict[str, Any]] = []
        _query_log_var.set(log)
        return log


def _before_cursor_execute(
    conn: Connection,
    _cursor: Any,
    _statement: str,
    _parameters: Any,
    _context: Any,
    _executemany: bool,  # ruff:ignore[boolean-type-hint-positional-argument]
) -> None:
    conn.info.setdefault("query_start_time", []).append(time.perf_counter())


def _after_cursor_execute(
    conn: Connection,
    _cursor: Any,
    statement: str,
    _parameters: Any,
    _context: Any,
    _executemany: bool,  # ruff:ignore[boolean-type-hint-positional-argument]
) -> None:
    total = time.perf_counter() - conn.info["query_start_time"].pop(-1)
    query_log = _get_query_log()
    query_log.append({"statement": statement, "duration_ms": round(total * 1000, 2)})


def install_profiling(engine: Engine) -> None:
    """Attach before/after cursor execute events to the engine."""
    event.listen(engine, "before_cursor_execute", _before_cursor_execute)
    event.listen(engine, "after_cursor_execute", _after_cursor_execute)


def reset_query_log() -> None:
    """Reset the query log for the current context with a fresh mutable list."""
    _query_log_var.set([])


def get_query_summary() -> dict[str, Any]:
    """Return summary of queries executed in the current context."""
    query_log = _get_query_log()
    total_ms = sum(q["duration_ms"] for q in query_log)
    return {
        "query_count": len(query_log),
        "total_sql_ms": round(total_ms, 2),
        "queries": query_log,
    }


def log_profile_summary(request: Request, route_template: Any, process_time: float) -> None:
    """Log SQL profiling summary and individual queries."""
    summary = get_query_summary()
    L.info(
        "PROFILE request_summary | {} {} | total={:.1f}ms | sql={:.1f}ms | queries={}",
        request.method,
        route_template or request.url.path,
        process_time * 1000,
        summary["total_sql_ms"],
        summary["query_count"],
    )
    n = settings.MAX_LOGGED_STATEMENT_LENGTH
    L.opt(lazy=True).info(
        "PROFILE queries:\n{}",
        lambda: "\n".join(
            f"  SQL[{i}] {q['duration_ms']:.1f}ms: {q['statement'][:n].replace('\n', ' ')}"
            for i, q in enumerate(summary["queries"])
        ),
    )


@contextmanager
def profile_section(label: str) -> Generator[None]:
    """Context manager to time a section and log it."""
    start = time.perf_counter()
    initial_count = len(_get_query_log())
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        final_count = len(_get_query_log())
        queries_in_section = final_count - initial_count
        L.info(
            "PROFILE [{}]: {:.1f}ms ({} queries)",
            label,
            elapsed * 1000,
            queries_in_section,
        )
