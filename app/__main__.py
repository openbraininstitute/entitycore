"""Main entrypoint"""

import click
import uvicorn


@click.group()
def cli():
    """Main CLI group"""


@cli.command()
@click.option("--host", default="0.0.0.0", help="Address to listen on to run on")
@click.option("--port", default=8000, help="Port to run on")
def run(host, port):
    """Run the application"""
    uvicorn.run("app:app", host=host, port=port)


@cli.group()
def db():
    """Database operations"""


@db.command()
def init():
    from app.models import init_db
    from app.config import settings

    click.secho(f"Connectiong to: {settings.DB_URI}", fg="green")
    init_db(settings.DB_URI)


if __name__ == "__main__":
    cli()
