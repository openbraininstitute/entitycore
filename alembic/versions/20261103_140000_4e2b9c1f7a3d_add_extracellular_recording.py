"""Add extracellular_recording

Revision ID: 4e2b9c1f7a3d
Revises: 3a6881ce006e
Create Date: 2026-11-03 14:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic_postgresql_enum import TableReference
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4e2b9c1f7a3d"
down_revision: Union[str, None] = "3a6881ce006e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "extracellular_recording",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("probe_names", postgresql.ARRAY(sa.VARCHAR()), nullable=False),
        sa.Column("channel_count", sa.Integer(), nullable=False),
        sa.Column("sampling_frequency", sa.Float(), nullable=False),
        sa.Column("duration", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["id"],
            ["electrical_recording.id"],
            name=op.f("fk_extracellular_recording_id_electrical_recording"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extracellular_recording")),
    )
    op.add_enum_value(
        enum_schema="public",
        enum_name="entitytype",
        new_value="extracellular_recording",
    )
    op.add_enum_value(
        enum_schema="public",
        enum_name="derivationtype",
        new_value="simulation_result_extracellular_recording",
        before_value="unspecified",
    )


def downgrade() -> None:
    op.sync_enum_values(
        enum_schema="public",
        enum_name="derivationtype",
        new_values=[
            "circuit_customization",
            "circuit_extraction",
            "circuit_rewiring",
            "emodel_circuit",
            "em_dense_reconstruction_dataset_cell_morphology",
            "circuit_simplification",
            "research_log_input",
            "research_log_output",
            "unspecified",
        ],
        affected_columns=[
            TableReference(
                table_schema="public", table_name="derivation", column_name="derivation_type"
            )
        ],
        enum_values_to_rename=[],
    )
    op.sync_enum_values(
        enum_schema="public",
        enum_name="entitytype",
        new_values=[
            "analysis_software_source_code",
            "brain_atlas",
            "brain_atlas_region",
            "cell_composition",
            "cell_morphology",
            "cell_morphology_protocol",
            "electrical_cell_recording",
            "electrical_recording",
            "electrical_recording_stimulus",
            "emodel",
            "task_result",
            "experimental_bouton_density",
            "experimental_neuron_density",
            "experimental_synapses_per_connection",
            "external_url",
            "ion_channel_model",
            "ion_channel_modeling_campaign",
            "ion_channel_modeling_config",
            "ion_channel_recording",
            "memodel",
            "memodel_calibration_result",
            "me_type_density",
            "simulation",
            "simulation_campaign",
            "simulation_result",
            "scientific_artifact",
            "single_neuron_simulation",
            "single_neuron_synaptome",
            "single_neuron_synaptome_simulation",
            "simulatable_extracellular_recording_array",
            "subject",
            "validation_result",
            "circuit",
            "em_dense_reconstruction_dataset",
            "em_cell_mesh",
            "analysis_notebook_template",
            "analysis_notebook_environment",
            "analysis_notebook_result",
            "skeletonization_config",
            "skeletonization_campaign",
            "task_config",
            "research_log",
        ],
        affected_columns=[
            TableReference(table_schema="public", table_name="entity", column_name="type"),
            TableReference(
                table_schema="public", table_name="measurement_label", column_name="entity_type"
            ),
        ],
        enum_values_to_rename=[],
    )
    op.drop_table("extracellular_recording")
