import uvicorn
from uvicorn.supervisors import ChangeReload

from app.logger import configure_logging


class CustomUvicornConfig(uvicorn.Config):
    """Class to be used when using loguru and running uvicorn with auto-reload enabled."""

    def configure_logging(self) -> None:
        """Re-configure logging in subprocesses when auto-reload is enabled."""
        super().configure_logging()
        configure_logging()


def run_server(app: str, *, host: str, port: int, reload: bool = False) -> None:
    config = CustomUvicornConfig(
        app,
        host=host,
        port=port,
        reload=reload,
        proxy_headers=True,
        log_config=None,
    )
    server = uvicorn.Server(config)
    if reload:
        sock = config.bind_socket()
        ChangeReload(config, target=server.run, sockets=[sock]).run()
    else:
        server.run()
