"""Add EMCellMesh and EMDenseReconstructionDataset

Revision ID: de87a4c88ded
Revises: b89af5e363b9
Create Date: 2025-09-11 12:19:14.642463

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic_postgresql_enum import TableReference
from alembic_utils.pg_trigger import PGTrigger
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "de87a4c88ded"
down_revision: Union[str, None] = "b89af5e363b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sa.Enum("static", "dynamic", name="emcellmeshtype").create(op.get_bind())
    sa.Enum("marching_cubes", name="emcellmeshgenerationmethod").create(op.get_bind())
    sa.Enum("coronal", "sagittal", "horizontal", "custom", name="slicingdirectiontype").create(
        op.get_bind()
    )
    op.create_table(
        "em_dense_reconstruction_dataset",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("protocol_document", sa.String(), nullable=True),
        sa.Column("fixation", sa.String(), nullable=True),
        sa.Column("staining_type", sa.String(), nullable=True),
        sa.Column("slicing_thickness", sa.Float(), nullable=True),
        sa.Column("tissue_shrinkage", sa.Float(), nullable=True),
        sa.Column("microscope_type", sa.String(), nullable=True),
        sa.Column("detector", sa.String(), nullable=True),
        sa.Column(
            "slicing_direction",
            postgresql.ENUM(
                "coronal",
                "sagittal",
                "horizontal",
                "custom",
                name="slicingdirectiontype",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("landmarks", sa.String(), nullable=True),
        sa.Column("voltage", sa.Float(), nullable=True),
        sa.Column("current", sa.Float(), nullable=True),
        sa.Column("dose", sa.Float(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("volume_resolution_x_nm", sa.Float(), nullable=False),
        sa.Column("volume_resolution_y_nm", sa.Float(), nullable=False),
        sa.Column("volume_resolution_z_nm", sa.Float(), nullable=False),
        sa.Column("release_url", sa.String(), nullable=False),
        sa.Column("cave_client_url", sa.String(), nullable=False),
        sa.Column("cave_datastack", sa.String(), nullable=False),
        sa.Column("precomputed_mesh_url", sa.String(), nullable=False),
        sa.Column("cell_identifying_property", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("description_vector", postgresql.TSVECTOR(), nullable=True),
        sa.ForeignKeyConstraint(
            ["id"],
            ["scientific_artifact.id"],
            name=op.f("fk_em_dense_reconstruction_dataset_id_scientific_artifact"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_em_dense_reconstruction_dataset")),
    )
    op.create_index(
        "ix_em_dense_reconstruction_dataset_description_vector",
        "em_dense_reconstruction_dataset",
        ["description_vector"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        op.f("ix_em_dense_reconstruction_dataset_name"),
        "em_dense_reconstruction_dataset",
        ["name"],
        unique=False,
    )
    op.create_table(
        "em_cell_mesh",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("em_dense_reconstruction_dataset_id", sa.Uuid(), nullable=False),
        sa.Column("release_version", sa.Integer(), nullable=False),
        sa.Column("dense_reconstruction_cell_id", sa.Integer(), nullable=False),
        sa.Column(
            "generation_method",
            postgresql.ENUM("marching_cubes", name="emcellmeshgenerationmethod", create_type=False),
            nullable=False,
        ),
        sa.Column("level_of_detail", sa.Integer(), nullable=False),
        sa.Column("generation_parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "mesh_type",
            postgresql.ENUM("static", "dynamic", name="emcellmeshtype", create_type=False),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["em_dense_reconstruction_dataset_id"],
            ["em_dense_reconstruction_dataset.id"],
            name=op.f(
                "fk_em_cell_mesh_em_dense_reconstruction_dataset_id_em_dense_reconstruction_dataset"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["id"], ["scientific_artifact.id"], name=op.f("fk_em_cell_mesh_id_scientific_artifact")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_em_cell_mesh")),
    )
    op.create_index(
        op.f("ix_em_cell_mesh_em_dense_reconstruction_dataset_id"),
        "em_cell_mesh",
        ["em_dense_reconstruction_dataset_id"],
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
    op.sync_enum_values(
        enum_schema="public",
        enum_name="assetlabel",
        new_values=[
            "morphology",
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
        ],
        affected_columns=[
            TableReference(table_schema="public", table_name="asset", column_name="label")
        ],
        enum_values_to_rename=[],
    )
    public_em_dense_reconstruction_dataset_em_dense_reconstruction_dataset_description_vector = PGTrigger(
        schema="public",
        signature="em_dense_reconstruction_dataset_description_vector",
        on_entity="public.em_dense_reconstruction_dataset",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON em_dense_reconstruction_dataset\n            FOR EACH ROW EXECUTE FUNCTION\n                tsvector_update_trigger(description_vector, 'pg_catalog.english', description, name)",
    )
    op.create_entity(
        public_em_dense_reconstruction_dataset_em_dense_reconstruction_dataset_description_vector
    )


def downgrade() -> None:
    public_em_dense_reconstruction_dataset_em_dense_reconstruction_dataset_description_vector = PGTrigger(
        schema="public",
        signature="em_dense_reconstruction_dataset_description_vector",
        on_entity="public.em_dense_reconstruction_dataset",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON em_dense_reconstruction_dataset\n            FOR EACH ROW EXECUTE FUNCTION\n                tsvector_update_trigger(description_vector, 'pg_catalog.english', description, name)",
    )
    op.drop_entity(
        public_em_dense_reconstruction_dataset_em_dense_reconstruction_dataset_description_vector
    )
    op.sync_enum_values(
        enum_schema="public",
        enum_name="assetlabel",
        new_values=[
            "morphology",
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
        ],
        affected_columns=[
            TableReference(table_schema="public", table_name="asset", column_name="label")
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
        ],
        affected_columns=[
            TableReference(table_schema="public", table_name="entity", column_name="type")
        ],
        enum_values_to_rename=[],
    )
    op.drop_index(
        op.f("ix_em_cell_mesh_em_dense_reconstruction_dataset_id"), table_name="em_cell_mesh"
    )
    op.drop_table("em_cell_mesh")
    op.drop_index(
        op.f("ix_em_dense_reconstruction_dataset_name"),
        table_name="em_dense_reconstruction_dataset",
    )
    op.drop_index(
        "ix_em_dense_reconstruction_dataset_description_vector",
        table_name="em_dense_reconstruction_dataset",
        postgresql_using="gin",
    )
    op.drop_table("em_dense_reconstruction_dataset")
    sa.Enum("coronal", "sagittal", "horizontal", "custom", name="slicingdirectiontype").drop(
        op.get_bind()
    )
    sa.Enum("marching_cubes", name="emcellmeshgenerationmethod").drop(op.get_bind())
    sa.Enum("static", "dynamic", name="emcellmeshtype").drop(op.get_bind())
