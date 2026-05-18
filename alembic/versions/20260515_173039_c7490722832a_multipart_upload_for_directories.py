"""Multipart upload for directories

Revision ID: c7490722832a
Revises: b8ebf9a4e3da
Create Date: 2026-05-15 17:30:39.752334

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic_postgresql_enum import TableReference
from alembic_postgresql_enum.sql_commands.indexes import TableIndex

from sqlalchemy import Text, text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "c7490722832a"
down_revision: Union[str, None] = "b8ebf9a4e3da"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Purge assets in status DELETED
    op.execute(text("""DELETE FROM asset WHERE status='DELETED'"""))
    # Add asset.parent_id
    op.add_column("asset", sa.Column("parent_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_asset_parent_id"), "asset", ["parent_id"], unique=False)
    op.create_foreign_key(op.f("fk_asset_parent_id_asset"), "asset", "asset", ["parent_id"], ["id"])
    # Remove the DELETED status from AssetStatus, not used anymore
    op.sync_enum_values(
        enum_schema="public",
        enum_name="assetstatus",
        new_values=["CREATED", "UPLOADING"],
        affected_columns=[
            TableReference(table_schema="public", table_name="asset", column_name="status")
        ],
        enum_values_to_rename=[],
        indexes_to_recreate=[
            TableIndex(
                name="public.ix_asset_full_path",
                definition="CREATE UNIQUE INDEX ix_asset_full_path ON public.asset USING btree (full_path)",
            ),
            TableIndex(
                name="public.uq_asset_entity_id_path",
                definition="CREATE UNIQUE INDEX uq_asset_entity_id_path ON public.asset USING btree (path, entity_id)",
            ),
        ],
    )
    # Add application/octet-stream to ContentType
    op.sync_enum_values(
        enum_schema="public",
        enum_name="contenttype",
        new_values=[
            "application/json",
            "application/swc",
            "application/nrrd",
            "application/obj",
            "application/hoc",
            "application/asc",
            "application/abf",
            "application/nwb",
            "application/x-hdf5",
            "text/plain",
            "application/vnd.directory",
            "application/mod",
            "application/pdf",
            "image/png",
            "image/jpeg",
            "model/gltf-binary",
            "application/gzip",
            "image/webp",
            "application/x-ipynb+json",
            "application/zip",
            "application/octet-stream",
        ],
        affected_columns=[
            TableReference(table_schema="public", table_name="asset", column_name="content_type")
        ],
        enum_values_to_rename=[],
    )
    # Add directory_child to AssetLabel
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
            "nwb",
            "neuron_hoc",
            "emodel_optimization_output",
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
        ],
        affected_columns=[
            TableReference(table_schema="public", table_name="asset", column_name="label")
        ],
        enum_values_to_rename=[],
    )


def downgrade() -> None:
    op.sync_enum_values(
        enum_schema="public",
        enum_name="assetlabel",
        new_values=[
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
            "nwb",
            "neuron_hoc",
            "emodel_optimization_output",
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
        ],
        affected_columns=[
            TableReference(table_schema="public", table_name="asset", column_name="label")
        ],
        enum_values_to_rename=[],
    )
    op.sync_enum_values(
        enum_schema="public",
        enum_name="contenttype",
        new_values=[
            "application/json",
            "application/swc",
            "application/nrrd",
            "application/obj",
            "application/hoc",
            "application/asc",
            "application/abf",
            "application/nwb",
            "application/x-hdf5",
            "text/plain",
            "application/vnd.directory",
            "application/mod",
            "application/pdf",
            "image/png",
            "image/jpeg",
            "model/gltf-binary",
            "application/gzip",
            "image/webp",
            "application/x-ipynb+json",
            "application/zip",
        ],
        affected_columns=[
            TableReference(table_schema="public", table_name="asset", column_name="content_type")
        ],
        enum_values_to_rename=[],
    )
    op.sync_enum_values(
        enum_schema="public",
        enum_name="assetstatus",
        new_values=["CREATED", "UPLOADING", "DELETED"],
        affected_columns=[
            TableReference(table_schema="public", table_name="asset", column_name="status")
        ],
        enum_values_to_rename=[],
        indexes_to_recreate=[
            TableIndex(
                name="public.ix_asset_full_path",
                definition="CREATE UNIQUE INDEX ix_asset_full_path ON public.asset USING btree (full_path) WHERE (status <> 'DELETED'::assetstatus)",
            ),
            TableIndex(
                name="public.uq_asset_entity_id_path",
                definition="CREATE UNIQUE INDEX uq_asset_entity_id_path ON public.asset USING btree (path, entity_id) WHERE (status <> 'DELETED'::assetstatus)",
            ),
        ],
    )
    op.drop_constraint(op.f("fk_asset_parent_id_asset"), "asset", type_="foreignkey")
    op.drop_index(op.f("ix_asset_parent_id"), table_name="asset")
    op.drop_column("asset", "parent_id")
