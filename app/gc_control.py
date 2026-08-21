"""Freeze startup objects, disable automatic GC, run gen1/gen2 on separate background intervals."""

import gc
import threading
import time
from collections.abc import Callable

from app.config import settings
from app.logger import L


def configure_gc() -> None:
    """Freeze existing objects and disable automatic GC."""
    gc.collect(2)
    gc.freeze()
    gc.disable()
    L.info("GC configured: frozen={} objects, automatic collection disabled", gc.get_freeze_count())


def _collect(generation: int, level: str = "debug") -> None:
    """Run gc.collect for the given generation and log results with timing."""
    t0 = time.monotonic()
    collected = gc.collect(generation)
    elapsed = time.monotonic() - t0
    if collected:
        L.log(
            level.upper(),
            "GC gen{} collected {} objects in {:.1f}ms",
            generation,
            collected,
            elapsed * 1000,
        )


def _gc_worker(stop: threading.Event, gen1_interval: float, gen2_interval: float) -> None:
    """Collect gen1 every gen1_interval seconds, gen2 every gen2_interval seconds."""
    last_gen2 = time.monotonic()
    while not stop.wait(timeout=gen1_interval):
        _collect(1, level="debug")

        now = time.monotonic()
        if now - last_gen2 >= gen2_interval:
            _collect(2, level="info")
            last_gen2 = now


def start_gc_thread() -> Callable[[], None]:
    """Start a daemon thread for periodic GC. Returns a stop function."""
    stop = threading.Event()
    thread = threading.Thread(
        target=_gc_worker,
        args=(stop, settings.GC_GEN1_INTERVAL_SECONDS, settings.GC_GEN2_INTERVAL_SECONDS),
        daemon=True,
        name="gc-worker",
    )
    thread.start()

    def shutdown() -> None:
        stop.set()
        thread.join(timeout=5)

    return shutdown
