"""GC control to eliminate latency spikes from gen2 collections.

After application startup (models loaded, routes registered), all long-lived objects are
moved to the permanent generation via gc.freeze(). Automatic collection is disabled and
replaced by a background daemon thread that periodically collects gen0+gen1 only, avoiding
stop-the-world gen2 pauses during request handling.
"""

import gc
import threading
import time

from app.config import settings
from app.logger import L


def configure_gc() -> None:
    """Freeze existing objects and disable automatic GC."""
    gc.collect(2)
    gc.freeze()
    gc.disable()
    L.info("GC configured: frozen={} objects, automatic collection disabled", gc.get_freeze_count())


def start_gc_thread() -> threading.Thread:
    """Start a daemon thread that runs gen0+gen1 collection periodically."""
    interval = settings.GC_INTERVAL_SECONDS

    def _gc_worker() -> None:
        while True:
            time.sleep(interval)
            collected = gc.collect(1)
            if collected:
                L.debug("Background GC collected {} objects", collected)

    thread = threading.Thread(target=_gc_worker, daemon=True, name="gc-worker")
    thread.start()
    return thread
