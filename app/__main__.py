"""Main entrypoint."""

import click

from app.logger import configure_logging
from app.utils.uvicorn import run_server


@click.group()
def cli():
    """Main CLI group."""


@cli.command()
@click.option("--host", default="0.0.0.0", help="Address to listen on to run on")
@click.option("--port", default=8000, help="Port to run on")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload.")
def run(host, port, reload):
    """Run the application."""
    run_server("app.application:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    """"""
    configure_logging()
    cli()
