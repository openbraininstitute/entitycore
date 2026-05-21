"""derivation_identifiable

Revision ID: 1df0fd1302f9
Revises: c7490722832a
Create Date: 2026-05-21 11:15:45.227116

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "1df0fd1302f9"
down_revision: Union[str, None] = "c7490722832a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OBI_ADMIN_PREF_LABEL = "OBI"


def upgrade() -> None:
    # Promote ``derivation`` to ``Identifiable``: add ``id`` PK plus ``created_by_id``,
    # ``updated_by_id``, ``creation_date`` and ``update_date``, and drop the old composite PK.
    # Existing rows are backfilled so that the migration can run on a populated database.

    # 1. Add ``id``. Use ``gen_random_uuid()`` (available in PG 13+ without pgcrypto) as a
    #    transient server default so every pre-existing row gets a fresh UUID. The column is
    #    initially nullable to keep the ``ADD COLUMN`` cheap on large tables; we'll flip it
    #    to NOT NULL after the implicit backfill from the server default.
    op.add_column(
        "derivation",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
    )

    # 2. Add ``created_by_id`` / ``updated_by_id`` as nullable so we can backfill them next.
    op.add_column("derivation", sa.Column("created_by_id", sa.Uuid(), nullable=True))
    op.add_column("derivation", sa.Column("updated_by_id", sa.Uuid(), nullable=True))

    # 3. ``creation_date`` / ``update_date`` have a server default, so they can be NOT NULL
    #    from the start; PostgreSQL will populate existing rows from ``now()``.
    op.add_column(
        "derivation",
        sa.Column(
            "creation_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "derivation",
        sa.Column(
            "update_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 4. Backfill ``created_by_id`` / ``updated_by_id`` for pre-existing derivations.
    #    Use the oldest agent in the system as a deterministic fallback "author". If
    #    ``derivation`` is empty (fresh database) no row is updated; if ``derivation`` is
    #    non-empty but ``agent`` is empty, the migration will fail at the NOT NULL alter
    #    below with a clear error, since we cannot synthesise a valid agent here.
    op.execute(
        f"""
        UPDATE derivation
        SET created_by_id = sub.agent_id,
            updated_by_id = sub.agent_id
        FROM (
            SELECT id AS agent_id
            FROM agent
            WHERE pref_label = '{OBI_ADMIN_PREF_LABEL}'
            LIMIT 1
        ) AS sub
        WHERE derivation.created_by_id IS NULL
           OR derivation.updated_by_id IS NULL
        """
    )

    # 5. Enforce NOT NULL now that all rows are populated.
    op.alter_column("derivation", "created_by_id", existing_type=sa.Uuid(), nullable=False)
    op.alter_column("derivation", "updated_by_id", existing_type=sa.Uuid(), nullable=False)

    # 6. Drop the transient server default on ``id`` so the schema matches a freshly created
    #    table (the application generates UUIDs in Python via ``app.utils.uuid.create_uuid``).
    op.execute("ALTER TABLE derivation ALTER COLUMN id DROP DEFAULT")

    # 7. Swap the primary key from (used_id, generated_id) to (id).
    op.drop_constraint(op.f("pk_derivation"), "derivation", type_="primary")
    op.create_primary_key(op.f("pk_derivation"), "derivation", ["id"])

    # 8. Indexes and foreign keys, identical to the auto-generated layout.
    op.create_index(
        op.f("ix_derivation_created_by_id"), "derivation", ["created_by_id"], unique=False
    )
    op.create_index(
        op.f("ix_derivation_creation_date"), "derivation", ["creation_date"], unique=False
    )
    op.create_index(
        op.f("ix_derivation_generated_id"), "derivation", ["generated_id"], unique=False
    )
    op.create_index(
        op.f("ix_derivation_updated_by_id"), "derivation", ["updated_by_id"], unique=False
    )
    op.create_index(op.f("ix_derivation_used_id"), "derivation", ["used_id"], unique=False)
    op.create_index(op.f("ix_derivation_derivation_type"), "derivation", ["derivation_type"], unique=False)
    op.create_foreign_key(
        op.f("fk_derivation_created_by_id_agent"),
        "derivation",
        "agent",
        ["created_by_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_derivation_updated_by_id_agent"),
        "derivation",
        "agent",
        ["updated_by_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_derivation_updated_by_id_agent"), "derivation", type_="foreignkey")
    op.drop_constraint(op.f("fk_derivation_created_by_id_agent"), "derivation", type_="foreignkey")
    op.drop_index(op.f("ix_derivation_used_id"), table_name="derivation")
    op.drop_index(op.f("ix_derivation_updated_by_id"), table_name="derivation")
    op.drop_index(op.f("ix_derivation_generated_id"), table_name="derivation")
    op.drop_index(op.f("ix_derivation_creation_date"), table_name="derivation")
    op.drop_index(op.f("ix_derivation_created_by_id"), table_name="derivation")
    op.drop_index(op.f("ix_derivation_derivation_type"), table_name="derivation")

    # Restore the old composite primary key on (used_id, generated_id). This will fail if
    # the table contains duplicate (used_id, generated_id) pairs that became possible after
    # the upgrade; such rows must be reconciled manually before downgrading.
    op.drop_constraint(op.f("pk_derivation"), "derivation", type_="primary")
    op.create_primary_key(op.f("pk_derivation"), "derivation", ["used_id", "generated_id"])

    op.drop_column("derivation", "update_date")
    op.drop_column("derivation", "creation_date")
    op.drop_column("derivation", "updated_by_id")
    op.drop_column("derivation", "created_by_id")
    op.drop_column("derivation", "id")
