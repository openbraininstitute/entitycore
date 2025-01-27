"""Main entrypoint."""

import click
import uvicorn


@click.group()
def cli():
    """Main CLI group."""


@cli.command()
@click.option("--host", default="0.0.0.0", help="Address to listen on to run on")
@click.option("--port", default=8000, help="Port to run on")
def run(host, port):
    """Run the application."""
    uvicorn.run("app:app", host=host, port=port)


if __name__ == "__main__":
    cli()
