import tracemalloc
from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel
from starlette.requests import Request

from app.config import settings
from app.dependencies.auth import AdminContextDep

router = APIRouter(
    prefix="/admin/debug",
    tags=["debug"],
    include_in_schema=False,
)

# Filters to exclude noise from tracemalloc results:
# - tracemalloc's own bookkeeping
# - importlib internals (frozen modules)
# - linecache (loaded by tracemalloc to display source lines)
_SNAPSHOT_FILTERS = [
    tracemalloc.Filter(inclusive=False, filename_pattern=tracemalloc.__file__),
    tracemalloc.Filter(inclusive=False, filename_pattern="<frozen importlib._bootstrap>"),
    tracemalloc.Filter(inclusive=False, filename_pattern="<frozen importlib._bootstrap_external>"),
    tracemalloc.Filter(inclusive=False, filename_pattern="<unknown>"),
]


class _MemoryAllocation(BaseModel):
    filename: str
    lineno: int
    size_kb: float
    count: int


class _MemoryAllocationDiff(BaseModel):
    filename: str
    lineno: int
    size_kb: float
    size_diff_kb: float
    count: int
    count_diff: int


class _MemorySnapshotResponse(BaseModel):
    enabled: bool
    baseline_taken_at: datetime | None = None
    snapshot_taken_at: datetime | None = None
    top: list[_MemoryAllocation]
    top_diff: list[_MemoryAllocationDiff]


def _to_allocations(stats: list) -> list[_MemoryAllocation]:
    return [
        _MemoryAllocation(
            filename=stat.traceback[0].filename,
            lineno=stat.traceback[0].lineno,
            size_kb=round(stat.size / 1024, 2),
            count=stat.count,
        )
        for stat in stats[: settings.TRACEMALLOC_TOP_N]
    ]


def _to_allocation_diffs(stats: list) -> list[_MemoryAllocationDiff]:
    return [
        _MemoryAllocationDiff(
            filename=stat.traceback[0].filename,
            lineno=stat.traceback[0].lineno,
            size_kb=round(stat.size / 1024, 2),
            size_diff_kb=round(stat.size_diff / 1024, 2),
            count=stat.count,
            count_diff=stat.count_diff,
        )
        for stat in stats[: settings.TRACEMALLOC_TOP_N]
    ]


@router.get("/memory")
def get_memory_snapshot(
    request: Request, _user_context: AdminContextDep
) -> _MemorySnapshotResponse:
    """Return top memory allocations and diff against the startup baseline.

    Requires TRACEMALLOC_ENABLED=true at startup.
    """
    if not settings.TRACEMALLOC_ENABLED or not tracemalloc.is_tracing():
        return _MemorySnapshotResponse(enabled=False, top=[], top_diff=[])

    now = datetime.now(tz=UTC)
    snapshot = tracemalloc.take_snapshot().filter_traces(_SNAPSHOT_FILTERS)
    baseline: tracemalloc.Snapshot | None = getattr(request.app.state, "tracemalloc_baseline", None)
    baseline_taken_at: datetime | None = getattr(request.app.state, "tracemalloc_baseline_at", None)

    if baseline is None:
        request.app.state.tracemalloc_baseline = snapshot
        request.app.state.tracemalloc_baseline_at = now
        return _MemorySnapshotResponse(
            enabled=True,
            baseline_taken_at=now,
            snapshot_taken_at=now,
            top=_to_allocations(snapshot.statistics("lineno")),
            top_diff=[],
        )

    diff_stats = snapshot.compare_to(baseline, "lineno")
    # Only show allocations that grew since baseline, sorted by size_diff descending
    growing = sorted(
        (s for s in diff_stats if s.size_diff > 0),
        key=lambda s: s.size_diff,
        reverse=True,
    )

    return _MemorySnapshotResponse(
        enabled=True,
        baseline_taken_at=baseline_taken_at,
        snapshot_taken_at=now,
        top=_to_allocations(snapshot.statistics("lineno")),
        top_diff=_to_allocation_diffs(growing),
    )


@router.post("/memory/reset")
def reset_memory_baseline(
    request: Request, _user_context: AdminContextDep
) -> _MemorySnapshotResponse:
    """Reset the tracemalloc baseline to the current snapshot.

    Use after warm-up to get a clean baseline for leak detection.
    Requires TRACEMALLOC_ENABLED=true at startup.
    """
    if not settings.TRACEMALLOC_ENABLED or not tracemalloc.is_tracing():
        return _MemorySnapshotResponse(enabled=False, top=[], top_diff=[])

    now = datetime.now(tz=UTC)
    snapshot = tracemalloc.take_snapshot().filter_traces(_SNAPSHOT_FILTERS)
    request.app.state.tracemalloc_baseline = snapshot
    request.app.state.tracemalloc_baseline_at = now

    return _MemorySnapshotResponse(
        enabled=True,
        baseline_taken_at=now,
        snapshot_taken_at=now,
        top=_to_allocations(snapshot.statistics("lineno")),
        top_diff=[],
    )
