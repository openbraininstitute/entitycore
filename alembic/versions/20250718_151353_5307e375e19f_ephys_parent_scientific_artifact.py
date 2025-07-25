"""ephys_parent_scientific_artifact

Revision ID: 5307e375e19f
Revises: 54eb4d0782bf
Create Date: 2025-07-18 15:13:53.548936

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "5307e375e19f"
down_revision: Union[str, None] = "54eb4d0782bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


electrical_cell_recording = sa.table(
    "electrical_cell_recording",
    sa.column("id", sa.UUID()),
    sa.column("subject_id", sa.UUID()),
    sa.column("brain_region_id", sa.UUID()),
    sa.column("license_id", sa.UUID()),
)


scientific_artifact = sa.table(
    "scientific_artifact",
    sa.column("id", sa.UUID()),
    sa.column("subject_id", sa.UUID()),
    sa.column("brain_region_id", sa.UUID()),
    sa.column("license_id", sa.UUID()),
)


def upgrade() -> None:
    conn = op.get_bind()

    missing_rows = conn.execute(
        sa.select(
            electrical_cell_recording.c.id,
            electrical_cell_recording.c.subject_id,
            electrical_cell_recording.c.brain_region_id,
            electrical_cell_recording.c.license_id,
        ).where(~electrical_cell_recording.c.id.in_(sa.select(scientific_artifact.c.id)))
    ).fetchall()

    if missing_rows:
        conn.execute(
            scientific_artifact.insert(),
            [
                {
                    "id": row.id,
                    "subject_id": row.subject_id,
                    "brain_region_id": row.brain_region_id,
                    "license_id": row.license_id,
                }
                for row in missing_rows
            ],
        )

    op.add_column("electrical_cell_recording", sa.Column("temperature", sa.Float(), nullable=True))
    op.drop_index(
        op.f("ix_electrical_cell_recording_brain_region_id"), table_name="electrical_cell_recording"
    )
    op.drop_index(
        op.f("ix_electrical_cell_recording_license_id"), table_name="electrical_cell_recording"
    )
    op.drop_index(
        op.f("ix_electrical_cell_recording_subject_id"), table_name="electrical_cell_recording"
    )
    op.drop_constraint(
        op.f("fk_electrical_cell_recording_license_id_license"),
        "electrical_cell_recording",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_electrical_cell_recording_subject_id_subject"),
        "electrical_cell_recording",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_electrical_cell_recording_brain_region_id_brain_region"),
        "electrical_cell_recording",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_electrical_cell_recording_id_entity"),
        "electrical_cell_recording",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_electrical_cell_recording_id_scientific_artifact"),
        "electrical_cell_recording",
        "scientific_artifact",
        ["id"],
        ["id"],
    )
    op.drop_column("electrical_cell_recording", "license_id")
    op.drop_column("electrical_cell_recording", "brain_region_id")
    op.drop_column("electrical_cell_recording", "subject_id")


def downgrade() -> None:
    # drop old foreign key first
    op.drop_constraint(
        "fk_electrical_cell_recording_id_scientific_artifact",
        "electrical_cell_recording",
        type_="foreignkey",
    )

    conn = op.get_bind()

    op.add_column(
        "electrical_cell_recording",
        sa.Column("subject_id", sa.UUID(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "electrical_cell_recording",
        sa.Column("brain_region_id", sa.UUID(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "electrical_cell_recording",
        sa.Column("license_id", sa.UUID(), autoincrement=False, nullable=True),
    )

    # Restore data from scientific_artifact to electrical_cell_recording
    update_stmt = (
        electrical_cell_recording.update()
        .values(
            {
                "subject_id": scientific_artifact.c.subject_id,
                "brain_region_id": scientific_artifact.c.brain_region_id,
                "license_id": scientific_artifact.c.license_id,
            }
        )
        .where(electrical_cell_recording.c.id == scientific_artifact.c.id)
    )
    conn.execute(update_stmt)

    # Delete scientific_artifact rows that were added during upgrade
    conn.execute(
        scientific_artifact.delete().where(
            scientific_artifact.c.id.in_(sa.select(electrical_cell_recording.c.id))
        )
    )

    op.create_foreign_key(
        op.f("fk_electrical_cell_recording_id_entity"),
        "electrical_cell_recording",
        "entity",
        ["id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_electrical_cell_recording_brain_region_id_brain_region"),
        "electrical_cell_recording",
        "brain_region",
        ["brain_region_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_electrical_cell_recording_subject_id_subject"),
        "electrical_cell_recording",
        "subject",
        ["subject_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_electrical_cell_recording_license_id_license"),
        "electrical_cell_recording",
        "license",
        ["license_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_electrical_cell_recording_subject_id"),
        "electrical_cell_recording",
        ["subject_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_electrical_cell_recording_license_id"),
        "electrical_cell_recording",
        ["license_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_electrical_cell_recording_brain_region_id"),
        "electrical_cell_recording",
        ["brain_region_id"],
        unique=False,
    )
    # make brain_region_id non-nullable after update
    op.alter_column(
        "electrical_cell_recording",
        "brain_region_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
    op.drop_column("electrical_cell_recording", "temperature")
