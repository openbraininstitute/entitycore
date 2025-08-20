"""Inherit ion_channel_model from scientific_artifact

Revision ID: 02b804d687ee
Revises: 80139d43afaf
Create Date: 2025-08-19 11:35:35.679039

"""

from typing import Sequence, Union
import uuid
import hashlib

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


from sqlalchemy import Connection

# revision identifiers, used by Alembic.
revision: str = "02b804d687ee"
down_revision: Union[str, None] = "80139d43afaf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

entity = sa.table(
    "entity",
    sa.column("id", sa.UUID()),
    sa.column("type", sa.TEXT()),
    sa.column("authorized_project_id", sa.UUID()),
    sa.column("authorized_public", sa.BOOLEAN()),
    sa.column("created_by_id", sa.UUID()),
    sa.column("updated_by_id", sa.UUID()),
)
scientific_artifact = sa.table(
    "scientific_artifact",
    sa.column("id", sa.UUID()),
    sa.column("subject_id", sa.UUID()),
    sa.column("brain_region_id", sa.UUID()),
    sa.column("license_id", sa.UUID()),
)
agent = sa.table(
    "agent",
    sa.column("id", sa.UUID()),
    sa.column("pref_label", sa.TEXT()),
)
ion_channel_model = sa.table(
    "ion_channel_model",
    sa.column("id", sa.UUID()),
    sa.column("species_id", sa.UUID()),
    sa.column("strain_id", sa.UUID()),
    sa.column("brain_region_id", sa.UUID()),
)
subject = sa.table(
    "subject",
    sa.column("id", sa.UUID()),
    sa.column("name", sa.TEXT()),
    sa.column("description", sa.TEXT()),
    sa.column("sex", sa.TEXT()),
    sa.column("species_id", sa.UUID()),
    sa.column("strain_id", sa.UUID()),
)
species = sa.table(
    "species",
    sa.column("id", sa.UUID()),
    sa.column("name", sa.TEXT()),
)
strain = sa.table(
    "strain",
    sa.column("id", sa.UUID()),
    sa.column("name", sa.TEXT()),
)

PUBLIC_PROJECT_ID = "0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6"
ADMIN_ID = "cd613e30-d8f1-4adf-91b7-584a2265b1f5"  # Admin/OBI


def _make_uuid(id_: uuid.UUID) -> uuid.UUID:
    """Make a new deterministic uuid from a given uuid.

    Not to be used when properly random uuids are needed!
    """
    h = hashlib.sha256(id_.bytes).digest()[:16]
    return uuid.UUID(bytes=h, version=4)


def _species_to_subject(conn: Connection) -> dict[uuid.UUID, dict]:
    """Return the mapping from species_id to generic subjects with deterministic uuids."""
    rows = conn.execute(sa.select(species.c.id, species.c.name)).all()
    return {
        row.id: {
            "id": _make_uuid(row.id),
            "name": f"Generic {row.name}",
        }
        for row in rows
    }


def _migrate_data() -> None:
    conn = op.get_bind()
    # add a generic subject for each existing species
    species_to_subject = _species_to_subject(conn)
    op.bulk_insert(
        entity,
        [
            {
                "id": subject["id"],
                "type": "subject",
                "authorized_project_id": PUBLIC_PROJECT_ID,
                "authorized_public": True,
                "created_by_id": ADMIN_ID,
                "updated_by_id": ADMIN_ID,
            }
            for _, subject in species_to_subject.items()
        ],
    )
    op.bulk_insert(
        subject,
        [
            {
                "id": subject["id"],
                "name": subject["name"],
                "description": "",
                "sex": "unknown",
                "species_id": species_id,
                "strain_id": None,
            }
            for species_id, subject in species_to_subject.items()
        ],
    )
    # insert a scientific_artifact for each ion_channel_model
    rows = conn.execute(
        sa.select(
            ion_channel_model.c.id,
            ion_channel_model.c.species_id,
            ion_channel_model.c.strain_id,
            ion_channel_model.c.brain_region_id,
        )
    ).all()
    for row in rows:
        if row.species_id not in species_to_subject:
            raise RuntimeError(f"Unhandled species_id: {row.species_id}")
        if row.strain_id is not None:
            # we don't expect any ion_channel_model with strain_id
            raise RuntimeError(f"Unhandled strain_id: {row.strain_id}")
    op.bulk_insert(
        scientific_artifact,
        [
            {
                "id": row.id,
                "subject_id": species_to_subject[row.species_id]["id"],
                "brain_region_id": row.brain_region_id,
                "license_id": None,  # license is missing in ion_channel_model
            }
            for row in rows
        ],
    )


def _restore_data() -> None:
    conn = op.get_bind()
    # update ion_channel_model from scientific_artifact and subject
    update_values = (
        sa.select(
            ion_channel_model.c.id,
            scientific_artifact.c.brain_region_id,
            subject.c.species_id,
            subject.c.strain_id,
        )
        .select_from(
            ion_channel_model.join(
                scientific_artifact,
                scientific_artifact.c.id == ion_channel_model.c.id,
            ).join(
                subject,
                subject.c.id == scientific_artifact.c.subject_id,
            )
        )
        .subquery("new_values")
    )
    update_ion_channel_model = (
        sa.update(ion_channel_model)
        .values(
            brain_region_id=update_values.c.brain_region_id,
            species_id=update_values.c.species_id,
            strain_id=update_values.c.strain_id,
        )
        .where(ion_channel_model.c.id == update_values.c.id)
    )
    conn.execute(update_ion_channel_model)
    # delete scientific_artifact rows inserted during upgrade
    conn.execute(
        sa.delete(scientific_artifact).where(
            scientific_artifact.c.id.in_(sa.select(ion_channel_model.c.id))
        )
    )
    # delete subject and entity rows inserted during upgrade
    species_to_subject = _species_to_subject(conn)
    subject_ids = [subject["id"] for subject in species_to_subject.values()]
    conn.execute(sa.delete(subject).where(subject.c.id.in_(subject_ids)))
    conn.execute(sa.delete(entity).where(entity.c.id.in_(subject_ids)))


def upgrade() -> None:
    _migrate_data()
    op.drop_index(op.f("ix_ion_channel_model_brain_region_id"), table_name="ion_channel_model")
    op.drop_index(op.f("ix_ion_channel_model_species_id"), table_name="ion_channel_model")
    op.drop_index(op.f("ix_ion_channel_model_strain_id"), table_name="ion_channel_model")
    op.drop_constraint(
        op.f("fk_ion_channel_model_id_entity"), "ion_channel_model", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_ion_channel_model_species_id_species"), "ion_channel_model", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_ion_channel_model_strain_id_species_id"), "ion_channel_model", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_ion_channel_model_brain_region_id_brain_region"),
        "ion_channel_model",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_ion_channel_model_id_scientific_artifact"),
        "ion_channel_model",
        "scientific_artifact",
        ["id"],
        ["id"],
    )
    op.drop_column("ion_channel_model", "species_id")
    op.drop_column("ion_channel_model", "brain_region_id")
    op.drop_column("ion_channel_model", "strain_id")
    op.alter_column(
        "subject",
        "sex",
        existing_type=postgresql.ENUM("male", "female", "unknown", name="sex"),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "subject",
        "sex",
        existing_type=postgresql.ENUM("male", "female", "unknown", name="sex"),
        nullable=True,
    )
    op.add_column(
        "ion_channel_model", sa.Column("strain_id", sa.UUID(), autoincrement=False, nullable=True)
    )
    op.add_column(
        "ion_channel_model",
        sa.Column("brain_region_id", sa.UUID(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "ion_channel_model", sa.Column("species_id", sa.UUID(), autoincrement=False, nullable=True)
    )
    op.drop_constraint(
        op.f("fk_ion_channel_model_id_scientific_artifact"), "ion_channel_model", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_ion_channel_model_brain_region_id_brain_region"),
        "ion_channel_model",
        "brain_region",
        ["brain_region_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_ion_channel_model_strain_id_species_id"),
        "ion_channel_model",
        "strain",
        ["strain_id", "species_id"],
        ["id", "species_id"],
    )
    op.create_foreign_key(
        op.f("fk_ion_channel_model_species_id_species"),
        "ion_channel_model",
        "species",
        ["species_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_ion_channel_model_id_entity"), "ion_channel_model", "entity", ["id"], ["id"]
    )
    op.create_index(
        op.f("ix_ion_channel_model_strain_id"), "ion_channel_model", ["strain_id"], unique=False
    )
    op.create_index(
        op.f("ix_ion_channel_model_species_id"), "ion_channel_model", ["species_id"], unique=False
    )
    op.create_index(
        op.f("ix_ion_channel_model_brain_region_id"),
        "ion_channel_model",
        ["brain_region_id"],
        unique=False,
    )
    # restore the previous data
    _restore_data()
    # make brain_region_id non-nullable after update
    op.alter_column(
        "ion_channel_model",
        "brain_region_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
    # make species_id non-nullable after update
    op.alter_column(
        "ion_channel_model",
        "species_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
