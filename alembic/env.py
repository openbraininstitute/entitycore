import logging
from collections.abc import Iterable
from logging.config import fileConfig

import alembic_postgresql_enum  # noqa: F401
from alembic.environment import MigrationContext
from alembic.operations import MigrationScript
from sqlalchemy import engine_from_config, pool, text

from alembic import context
from app.config import settings
from app.db import triggers
from app.db.model import Base

L = logging.getLogger("alembic.env")

# server settings to reduce possible service disruptions while running the migration
SERVER_SETTINGS = {
    # Abort any statement that takes more than the specified amount of time
    "statement_timeout": "6000",
    # Abort any statement that waits longer than the specified amount of time while
    # attempting to acquire a lock on a table, index, row, or other database object
    "lock_timeout": "4000",
}

# register triggers only if alembic is run with `-x register_triggers="true"`
if context.get_x_argument(as_dictionary=True).get("register_triggers") == "true":
    triggers.register_all()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# use a %% to escape the % sign (% is the only character that needs to be escaped)
config.set_main_option("sqlalchemy.url", settings.DB_URI.replace("%", "%%"))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def process_revision_directives(
    _context: MigrationContext,
    _revision: str | Iterable[str | None] | Iterable[str],
    directives: list[MigrationScript],
) -> None:
    """Don't Generate Empty Migrations with Autogenerate.

    From https://alembic.sqlalchemy.org/en/latest/cookbook.html
    """
    assert config.cmd_opts is not None
    if getattr(config.cmd_opts, "autogenerate", False):
        script = directives[0]
        assert script.upgrade_ops is not None
        if script.upgrade_ops.is_empty():
            L.info("Ignoring empty migration")
            directives[:] = []


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={
            "options": " ".join(f"-c {key}={value}" for key, value in SERVER_SETTINGS.items()),
            "application_name": "alembic",
        },
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            transaction_per_migration=False,
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            # obtain an exclusive transaction-level advisory lock, waiting if necessary
            connection.execute(text("SELECT pg_advisory_xact_lock(12345)"))
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
