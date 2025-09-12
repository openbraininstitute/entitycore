"""Populate electrical_cell_recording ids.

Revision ID: 06af11530839
Revises: de87a4c88ded
Create Date: 2025-09-12 17:20:25.828230

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic_postgresql_enum import TableReference

from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "06af11530839"
down_revision: Union[str, None] = "de87a4c88ded"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # add missing records into electrical_cell_recording
    # caused by migrations d58bc70ec10f and b352b28dae67
    op.execute(
        """
        INSERT INTO electrical_cell_recording (id)
        SELECT e.id
        FROM entity e
        JOIN electrical_recording er ON e.id = er.id
        WHERE e.type = 'electrical_cell_recording'
        ON CONFLICT (id) DO NOTHING
        """
    )
    # remove mesh type
    op.sync_enum_values(
        enum_schema="public",
        enum_name="entitytype",
        new_values=[
            "analysis_software_source_code",
            "brain_atlas",
            "brain_atlas_region",
            "cell_composition",
            "electrical_cell_recording",
            "electrical_recording",
            "electrical_recording_stimulus",
            "emodel",
            "experimental_bouton_density",
            "experimental_neuron_density",
            "experimental_synapses_per_connection",
            "external_url",
            "ion_channel",
            "ion_channel_model",
            "ion_channel_recording",
            "memodel",
            "memodel_calibration_result",
            "me_type_density",
            "reconstruction_morphology",
            "simulation",
            "simulation_campaign",
            "simulation_campaign_generation",
            "simulation_execution",
            "simulation_result",
            "scientific_artifact",
            "single_neuron_simulation",
            "single_neuron_synaptome",
            "single_neuron_synaptome_simulation",
            "subject",
            "validation_result",
            "circuit",
            "em_dense_reconstruction_dataset",
            "em_cell_mesh",
        ],
        affected_columns=[
            TableReference(table_schema="public", table_name="entity", column_name="type")
        ],
        enum_values_to_rename=[],
    )


def downgrade() -> None:
    # restore mesh type
    op.sync_enum_values(
        enum_schema="public",
        enum_name="entitytype",
        new_values=[
            "analysis_software_source_code",
            "brain_atlas",
            "brain_atlas_region",
            "cell_composition",
            "electrical_cell_recording",
            "electrical_recording",
            "electrical_recording_stimulus",
            "emodel",
            "experimental_bouton_density",
            "experimental_neuron_density",
            "experimental_synapses_per_connection",
            "external_url",
            "ion_channel",
            "ion_channel_model",
            "ion_channel_recording",
            "memodel",
            "mesh",
            "memodel_calibration_result",
            "me_type_density",
            "reconstruction_morphology",
            "simulation",
            "simulation_campaign",
            "simulation_campaign_generation",
            "simulation_execution",
            "simulation_result",
            "scientific_artifact",
            "single_neuron_simulation",
            "single_neuron_synaptome",
            "single_neuron_synaptome_simulation",
            "subject",
            "validation_result",
            "circuit",
            "em_dense_reconstruction_dataset",
            "em_cell_mesh",
        ],
        affected_columns=[
            TableReference(table_schema="public", table_name="entity", column_name="type")
        ],
        enum_values_to_rename=[],
    )
