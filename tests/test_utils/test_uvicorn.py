import uvicorn

from app.utils import uvicorn as test_module


def test_custom_config_configure_logging_invokes_app_logging(monkeypatch):
    """CustomUvicornConfig.configure_logging re-applies the app logging/warnings setup.

    Uvicorn calls this hook in reload subprocesses, so the override must both delegate
    to the base implementation and re-configure loguru and the warnings filter.
    """
    calls = []

    # Avoid touching the real logging configuration during the test.
    monkeypatch.setattr(uvicorn.Config, "configure_logging", lambda _self: calls.append("super"))
    monkeypatch.setattr(test_module, "configure_logging", lambda: calls.append("logging"))
    monkeypatch.setattr(test_module, "configure_warnings", lambda: calls.append("warnings"))

    config = test_module.CustomUvicornConfig("app:app", host="127.0.0.1", port=8000)

    # uvicorn.Config.__init__ already triggers configure_logging once; ignore those calls
    # and assert on an explicit invocation (the case that matters in reload subprocesses).
    calls.clear()
    config.configure_logging()

    # The base implementation must run first, then the app-specific configuration.
    assert calls == ["super", "logging", "warnings"]


def test_run_server_without_reload_runs_server_directly(monkeypatch):
    """Without reload, run_server builds a Server from the config and runs it in-process."""
    created = {}

    class FakeServer:
        def __init__(self, config):
            created["config"] = config
            self.run_called = False

        def run(self):
            self.run_called = True
            created["server"] = self

    def _fail_bind_socket(_self):
        # bind_socket must never be called on the non-reload path.
        msg = "bind_socket should not be called when reload is disabled"
        raise AssertionError(msg)

    monkeypatch.setattr(test_module.uvicorn, "Server", FakeServer)
    monkeypatch.setattr(
        test_module.CustomUvicornConfig, "bind_socket", _fail_bind_socket, raising=True
    )

    test_module.run_server("app:app", host="0.0.0.0", port=9000, reload=False, root_path="/api")

    config = created["config"]
    assert isinstance(config, test_module.CustomUvicornConfig)
    assert config.host == "0.0.0.0"
    assert config.port == 9000
    assert config.root_path == "/api"
    assert config.proxy_headers is True
    assert created["server"].run_called is True


def test_run_server_with_reload_uses_change_reload(monkeypatch):
    """With reload, run_server binds a socket and drives the server through ChangeReload."""
    sentinel_socket = object()
    captured = {}

    class FakeServer:
        def __init__(self, config):
            captured["config"] = config

        @staticmethod
        def run():  # pragma: no cover - replaced by ChangeReload orchestration
            msg = "server.run should not be called directly when reload is enabled"
            raise AssertionError(msg)

    class FakeChangeReload:
        def __init__(self, config, *, target, sockets):
            captured["cr_config"] = config
            captured["target"] = target
            captured["sockets"] = sockets

        @staticmethod
        def run():
            captured["change_reload_run"] = True

    monkeypatch.setattr(test_module.uvicorn, "Server", FakeServer)
    monkeypatch.setattr(test_module, "ChangeReload", FakeChangeReload)
    # Return a sentinel socket instead of actually binding a port.
    monkeypatch.setattr(
        test_module.CustomUvicornConfig,
        "bind_socket",
        lambda _self: sentinel_socket,
        raising=True,
    )

    test_module.run_server("app:app", host="127.0.0.1", port=8080, reload=True)

    assert captured["change_reload_run"] is True
    # The bound socket is forwarded to ChangeReload.
    assert captured["sockets"] == [sentinel_socket]
    # The same config is shared between the server and the reloader.
    assert captured["cr_config"] is captured["config"]
    assert captured["cr_config"].reload is True


def test_run_server_defaults(monkeypatch):
    """run_server defaults to no reload and an empty root_path."""
    captured = {}

    class FakeServer:
        def __init__(self, config):
            captured["config"] = config

        @staticmethod
        def run():
            captured["run_called"] = True

    monkeypatch.setattr(test_module.uvicorn, "Server", FakeServer)

    test_module.run_server("app:app", host="localhost", port=1234)

    config = captured["config"]
    assert config.should_reload is False
    assert not config.root_path
    assert captured["run_called"] is True
