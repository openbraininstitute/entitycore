"""Default migration message

Revision ID: 0e7a384a6428
Revises: 1a5cec5b629b
Create Date: 2025-06-06 08:58:28.572563

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic_postgresql_enum import TableReference
from sqlalchemy.dialects import postgresql

from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "0e7a384a6428"
down_revision: Union[str, None] = "1a5cec5b629b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    sa.Enum(
        "created", "pending", "running", "done", "error", name="simulation_execution_status"
    ).create(op.get_bind())
    sa.Enum("simulation_execution", "simulation_generation", name="activitytype").create(
        op.get_bind()
    )
    op.create_table(
        "activity",
        sa.Column(
            "type",
            postgresql.ENUM(
                "simulation_execution",
                "simulation_generation",
                name="activitytype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("updated_by_id", sa.Uuid(), nullable=False),
        sa.Column(
            "creation_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "update_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["agent.id"], name=op.f("fk_activity_created_by_id_agent")
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_id"], ["agent.id"], name=op.f("fk_activity_updated_by_id_agent")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_activity")),
    )
    op.create_index(op.f("ix_activity_created_by_id"), "activity", ["created_by_id"], unique=False)
    op.create_index(op.f("ix_activity_creation_date"), "activity", ["creation_date"], unique=False)
    op.create_index(op.f("ix_activity_updated_by_id"), "activity", ["updated_by_id"], unique=False)
    op.create_table(
        "generation",
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("activity_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["activity_id"], ["activity.id"], name=op.f("fk_generation_activity_id_activity")
        ),
        sa.ForeignKeyConstraint(
            ["entity_id"], ["entity.id"], name=op.f("fk_generation_entity_id_entity")
        ),
        sa.PrimaryKeyConstraint("entity_id", "activity_id", name=op.f("pk_generation")),
        sa.UniqueConstraint("entity_id", "activity_id", name="uq_generation_entity_id_activity_id"),
    )
    op.create_table(
        "simulation_campaign",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("description_vector", postgresql.TSVECTOR(), nullable=True),
        sa.ForeignKeyConstraint(
            ["id"], ["entity.id"], name=op.f("fk_simulation_campaign_id_entity")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_simulation_campaign")),
    )
    op.create_index(
        "ix_simulation_campaign_description_vector",
        "simulation_campaign",
        ["description_vector"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        op.f("ix_simulation_campaign_name"), "simulation_campaign", ["name"], unique=False
    )
    op.create_table(
        "simulation_execution",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "created",
                "pending",
                "running",
                "done",
                "error",
                name="simulation_execution_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["id"], ["activity.id"], name=op.f("fk_simulation_execution_id_activity")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_simulation_execution")),
    )
    op.create_table(
        "simulation_generation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["id"], ["activity.id"], name=op.f("fk_simulation_generation_id_activity")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_simulation_generation")),
    )
    op.create_table(
        "simulation_report",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["id"], ["entity.id"], name=op.f("fk_simulation_report_id_entity")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_simulation_report")),
    )
    op.create_table(
        "usage",
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("activity_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["activity_id"], ["activity.id"], name=op.f("fk_usage_activity_id_activity")
        ),
        sa.ForeignKeyConstraint(
            ["entity_id"], ["entity.id"], name=op.f("fk_usage_entity_id_entity")
        ),
        sa.PrimaryKeyConstraint("entity_id", "activity_id", name=op.f("pk_usage")),
        sa.UniqueConstraint("entity_id", "activity_id", name="uq_usage_entity_id_activity_id"),
    )
    op.create_table(
        "simulation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("simulation_campaign_id", sa.Uuid(), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column(
            "scan_parameters",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["entity_id"], ["entity.id"], name=op.f("fk_simulation_entity_id_entity")
        ),
        sa.ForeignKeyConstraint(["id"], ["entity.id"], name=op.f("fk_simulation_id_entity")),
        sa.ForeignKeyConstraint(
            ["simulation_campaign_id"],
            ["simulation_campaign.id"],
            name=op.f("fk_simulation_simulation_campaign_id_simulation_campaign"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_simulation")),
    )
    op.create_index(op.f("ix_simulation_entity_id"), "simulation", ["entity_id"], unique=False)
    op.create_index(
        op.f("ix_simulation_simulation_campaign_id"),
        "simulation",
        ["simulation_campaign_id"],
        unique=False,
    )
    op.sync_enum_values(
        enum_schema="public",
        enum_name="entitytype",
        new_values=[
            "analysis_software_source_code",
            "brain_atlas",
            "brain_atlas_region",
            "cell_composition",
            "electrical_cell_recording",
            "electrical_recording_stimulus",
            "emodel",
            "experimental_bouton_density",
            "experimental_neuron_density",
            "experimental_synapses_per_connection",
            "ion_channel_model",
            "memodel",
            "mesh",
            "memodel_calibration_result",
            "me_type_density",
            "publication",
            "reconstruction_morphology",
            "simulation",
            "simulation_campaign",
            "simulation_campaign_generation",
            "simulation_execution",
            "simulation_report",
            "scientific_artifact",
            "single_neuron_simulation",
            "single_neuron_synaptome",
            "single_neuron_synaptome_simulation",
            "subject",
            "validation_result",
            "circuit",
        ],
        affected_columns=[
            TableReference(table_schema="public", table_name="entity", column_name="type")
        ],
        enum_values_to_rename=[],
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.sync_enum_values(
        enum_schema="public",
        enum_name="entitytype",
        new_values=[
            "analysis_software_source_code",
            "brain_atlas",
            "brain_atlas_region",
            "cell_composition",
            "electrical_cell_recording",
            "electrical_recording_stimulus",
            "emodel",
            "experimental_bouton_density",
            "experimental_neuron_density",
            "experimental_synapses_per_connection",
            "ion_channel_model",
            "memodel",
            "mesh",
            "memodel_calibration_result",
            "me_type_density",
            "publication",
            "reconstruction_morphology",
            "scientific_artifact",
            "single_neuron_simulation",
            "single_neuron_synaptome",
            "single_neuron_synaptome_simulation",
            "subject",
            "validation_result",
            "circuit",
        ],
        affected_columns=[
            TableReference(table_schema="public", table_name="entity", column_name="type")
        ],
        enum_values_to_rename=[],
    )
    op.drop_index(op.f("ix_simulation_simulation_campaign_id"), table_name="simulation")
    op.drop_index(op.f("ix_simulation_entity_id"), table_name="simulation")
    op.drop_table("simulation")
    op.drop_table("usage")
    op.drop_table("simulation_report")
    op.drop_table("simulation_generation")
    op.drop_table("simulation_execution")
    op.drop_index(op.f("ix_simulation_campaign_name"), table_name="simulation_campaign")
    op.drop_index(
        "ix_simulation_campaign_description_vector",
        table_name="simulation_campaign",
        postgresql_using="gin",
    )
    op.drop_table("simulation_campaign")
    op.drop_table("generation")
    op.drop_index(op.f("ix_activity_updated_by_id"), table_name="activity")
    op.drop_index(op.f("ix_activity_creation_date"), table_name="activity")
    op.drop_index(op.f("ix_activity_created_by_id"), table_name="activity")
    op.drop_table("activity")
    sa.Enum("simulation_execution", "simulation_generation", name="activitytype").drop(
        op.get_bind()
    )
    sa.Enum(
        "created", "pending", "running", "done", "error", name="simulation_execution_status"
    ).drop(op.get_bind())
    # ### end Alembic commands ###
