"""add compartment_sets asset label

Revision ID: e5c06332b31c
Revises: 480ae265c9e9
Create Date: 2026-07-20 15:09:13.022347

"""

from typing import Sequence, Union

from alembic import op
from alembic_postgresql_enum import TableReference

# revision identifiers, used by Alembic.
revision: str = "e5c06332b31c"
down_revision: Union[str, None] = "480ae265c9e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE public.assetlabel ADD VALUE IF NOT EXISTS 'compartment_sets'")


def downgrade() -> None:
    op.sync_enum_values(
        enum_schema="public",
        enum_name="assetlabel",
        new_values=[
            "directory_child",
            "morphology",
            "morphology_with_spines",
            "cell_composition_summary",
            "cell_composition_volumes",
            "single_neuron_synaptome_config",
            "single_neuron_synaptome_simulation_data",
            "single_neuron_simulation_data",
            "sonata_circuit",
            "compressed_sonata_circuit",
            "circuit_figures",
            "circuit_analysis_data",
            "circuit_connectivity_matrices",
            "task_result",
            "nwb",
            "neuron_hoc",
            "electrode_locations",
            "emodel_optimization_output",
            "emodel_optimisation_checkpoint",
            "emodel_analysis_figures",
            "emodel_analysis_summary",
            "sonata_simulation_config",
            "simulation_generation_config",
            "ion_channel_modeling_generation_config",
            "custom_node_sets",
            "campaign_generation_config",
            "campaign_summary",
            "replay_spikes",
            "voltage_report",
            "spike_report",
            "neuron_mechanisms",
            "brain_atlas_annotation",
            "brain_atlas_region_mesh",
            "voxel_densities",
            "validation_result_figure",
            "validation_result_details",
            "simulation_designer_image",
            "circuit_visualization",
            "node_stats",
            "network_stats_a",
            "network_stats_b",
            "cell_surface_mesh",
            "jupyter_notebook",
            "requirements",
            "notebook_required_files",
            "ion_channel_model_figure",
            "ion_channel_model_figure_summary_json",
            "ion_channel_model_thumbnail",
            "circuit_extraction_config",
            "skeletonization_config",
            "task_config",
            "lod_mesh_block",
            "electrode_array_weight_matrix",
            "electrode_array_image",
            "efeature_extraction_features",
            "efeature_extraction_figures",
            "efeature_extraction_cells",
            "efeature_extraction_protocols",
        ],
        affected_columns=[
            TableReference(table_schema="public", table_name="asset", column_name="label")
        ],
        enum_values_to_rename=[],
    )
