import threading
from unittest.mock import MagicMock, patch

from app import gc_control as test_module
from app.gc_control import _collect, _gc_worker, configure_gc, start_gc_thread


def test_configure_gc(monkeypatch):
    mock_gc = MagicMock()
    mock_gc.get_freeze_count.return_value = 42
    monkeypatch.setattr(test_module, "gc", mock_gc)
    monkeypatch.setattr(test_module, "L", MagicMock())

    configure_gc()

    mock_gc.collect.assert_called_once_with(2)
    mock_gc.freeze.assert_called_once()
    mock_gc.disable.assert_called_once()


def test_collect_logs_when_objects_collected(monkeypatch):
    mock_gc = MagicMock()
    mock_gc.collect.return_value = 7
    mock_time = MagicMock()
    mock_time.monotonic.side_effect = [0.0, 0.002]
    mock_log = MagicMock()
    monkeypatch.setattr(test_module, "gc", mock_gc)
    monkeypatch.setattr(test_module, "time", mock_time)
    monkeypatch.setattr(test_module, "L", mock_log)

    _collect(1, level="debug")

    mock_gc.collect.assert_called_once_with(1)
    mock_log.log.assert_called_once()


def test_collect_silent_when_nothing_collected(monkeypatch):
    mock_gc = MagicMock()
    mock_gc.collect.return_value = 0
    mock_time = MagicMock()
    mock_time.monotonic.side_effect = [0.0, 0.001]
    mock_log = MagicMock()
    monkeypatch.setattr(test_module, "gc", mock_gc)
    monkeypatch.setattr(test_module, "time", mock_time)
    monkeypatch.setattr(test_module, "L", mock_log)

    _collect(2, level="info")

    mock_gc.collect.assert_called_once_with(2)
    mock_log.log.assert_not_called()


def test_gc_worker_collects_gen1(monkeypatch):
    """Worker collects gen1 on each iteration."""
    stop = threading.Event()
    call_count = 0

    def fake_wait(timeout=None):  # ruff:ignore[unused-function-argument]
        nonlocal call_count
        call_count += 1
        return call_count > 1

    mock_collect = MagicMock()
    mock_time = MagicMock()
    mock_time.monotonic.return_value = 0.0
    monkeypatch.setattr(test_module, "_collect", mock_collect)
    monkeypatch.setattr(test_module, "time", mock_time)

    with patch.object(stop, "wait", side_effect=fake_wait):
        _gc_worker(stop, gen1_interval=5.0, gen2_interval=600.0)

    mock_collect.assert_called_with(1, level="debug")


def test_gc_worker_collects_gen2_when_interval_elapsed(monkeypatch):
    """Worker collects gen2 when gen2_interval has elapsed."""
    stop = threading.Event()
    call_count = 0

    def wait_once(timeout=None):  # ruff:ignore[unused-function-argument]
        nonlocal call_count
        call_count += 1
        return call_count > 1

    mock_collect = MagicMock()
    mock_time = MagicMock()
    mock_time.monotonic.side_effect = [0.0, 601.0]
    monkeypatch.setattr(test_module, "_collect", mock_collect)
    monkeypatch.setattr(test_module, "time", mock_time)

    with patch.object(stop, "wait", side_effect=wait_once):
        _gc_worker(stop, gen1_interval=5.0, gen2_interval=600.0)

    calls = [(c.args, c.kwargs) for c in mock_collect.call_args_list]
    assert calls == [((1,), {"level": "debug"}), ((2,), {"level": "info"})]


def test_gc_worker_skips_gen2_when_interval_not_elapsed(monkeypatch):
    """Worker does not collect gen2 before gen2_interval."""
    stop = threading.Event()
    call_count = 0

    def wait_once(timeout=None):  # ruff:ignore[unused-function-argument]
        nonlocal call_count
        call_count += 1
        return call_count > 1

    mock_collect = MagicMock()
    mock_time = MagicMock()
    mock_time.monotonic.return_value = 5.0
    monkeypatch.setattr(test_module, "_collect", mock_collect)
    monkeypatch.setattr(test_module, "time", mock_time)

    with patch.object(stop, "wait", side_effect=wait_once):
        _gc_worker(stop, gen1_interval=5.0, gen2_interval=600.0)

    calls = [(c.args, c.kwargs) for c in mock_collect.call_args_list]
    assert calls == [((1,), {"level": "debug"})]


def test_start_gc_thread_returns_stop_function(monkeypatch):
    """start_gc_thread returns a callable that stops the worker."""
    monkeypatch.setattr(test_module, "_collect", MagicMock())

    stop_gc = start_gc_thread()

    assert callable(stop_gc)
    stop_gc()
