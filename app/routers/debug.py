import tracemalloc

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


class _MemoryAllocation(BaseModel):
    filename: str
    lineno: int
    size_kb: float
    count: int


class _MemorySnapshotResponse(BaseModel):
    enabled: bool
    top: list[_MemoryAllocation]
    top_diff: list[_MemoryAllocation]


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


@router.get("/memory")
def get_memory_snapshot(
    request: Request, _user_context: AdminContextDep
) -> _MemorySnapshotResponse:
    """Return top memory allocations and diff against the startup baseline.

    Requires TRACEMALLOC_ENABLED=true at startup.
    """
    if not settings.TRACEMALLOC_ENABLED or not tracemalloc.is_tracing():
        return _MemorySnapshotResponse(enabled=False, top=[], top_diff=[])

    snapshot = tracemalloc.take_snapshot()
    baseline: tracemalloc.Snapshot | None = getattr(request.app.state, "tracemalloc_baseline", None)

    if baseline is None:
        request.app.state.tracemalloc_baseline = snapshot
        return _MemorySnapshotResponse(
            enabled=True, top=_to_allocations(snapshot.statistics("lineno")), top_diff=[]
        )

    return _MemorySnapshotResponse(
        enabled=True,
        top=_to_allocations(snapshot.statistics("lineno")),
        top_diff=_to_allocations(
            [s for s in snapshot.compare_to(baseline, "lineno") if s.size_diff > 0]
        ),
    )
