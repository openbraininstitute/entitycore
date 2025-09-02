"""Replace reconstruction_morphology with cell_morphology.

Revision ID: 7f8e31734e4c
Revises: 02b804d687ee
Create Date: 2025-08-26 15:33:59.497711

"""

import hashlib
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from alembic_postgresql_enum import TableReference
from sqlalchemy.dialects import postgresql

from sqlalchemy import Connection, Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "7f8e31734e4c"
down_revision: Union[str, None] = "02b804d687ee"
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
reconstruction_morphology = sa.table(
    "reconstruction_morphology",
    sa.column("id", sa.UUID()),
    sa.column("species_id", sa.UUID()),
    sa.column("strain_id", sa.UUID()),
    sa.column("brain_region_id", sa.UUID()),
    sa.column("license_id", sa.UUID()),
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
    sa.column("species_id", sa.UUID()),
)

PUBLIC_PROJECT_ID = "0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6"
ADMIN_ID = "cd613e30-d8f1-4adf-91b7-584a2265b1f5"  # Admin/OBI


def _make_uuid(*uuids: uuid.UUID) -> uuid.UUID:
    """Make a new deterministic uuid from one or more given UUIDs.

    Not to be used when properly random uuids are needed!
    """
    h = hashlib.sha256()
    for u in uuids:
        if u:
            h.update(u.bytes)
    return uuid.UUID(bytes=h.digest()[:16], version=4)


def _species_strain_to_subject(conn: Connection) -> dict[tuple, dict]:
    """Return a dict (species_id, strain_id) -> subject using deterministic subject UUIDs."""
    species_rows = conn.execute(
        sa.select(
            species.c.id.label("species_id"),
            species.c.name.label("species_name"),
        )
    ).all()
    strain_rows = conn.execute(
        sa.select(
            strain.c.id.label("strain_id"),
            strain.c.name.label("strain_name"),
            strain.c.species_id,
            species.c.name.label("species_name"),
        ).join_from(strain, species, strain.c.species_id == species.c.id)
    ).all()
    return {
        (row.species_id, None): {
            "id": _make_uuid(row.species_id),
            "name": f"Generic {row.species_name}",
        }
        for row in species_rows
    } | {
        (row.species_id, row.strain_id): {
            "id": _make_uuid(row.species_id, row.strain_id),
            "name": f"Generic {row.species_name}/{row.strain_name}",
        }
        for row in strain_rows
    }


def _insert_missing_subjects(
    conn: Connection, species_strain_to_subject: dict[tuple[uuid.UUID, uuid.UUID], dict]
) -> None:
    if species_strain_to_subject:
        conn.execute(
            postgresql.insert(entity).on_conflict_do_nothing(index_elements=["id"]),
            [
                {
                    "id": subject["id"],
                    "type": "subject",
                    "authorized_project_id": PUBLIC_PROJECT_ID,
                    "authorized_public": True,
                    "created_by_id": ADMIN_ID,
                    "updated_by_id": ADMIN_ID,
                }
                for _, subject in species_strain_to_subject.items()
            ],
        )
        conn.execute(
            postgresql.insert(subject).on_conflict_do_nothing(index_elements=["id"]),
            [
                {
                    "id": subject["id"],
                    "name": subject["name"],
                    "description": "",
                    "sex": "unknown",
                    "species_id": species_id,
                    "strain_id": strain_id,
                }
                for (species_id, strain_id), subject in species_strain_to_subject.items()
            ],
        )


def _migrate_data() -> None:
    conn = op.get_bind()

    # get the generic subject for each existing species and strain
    species_strain_to_subject = _species_strain_to_subject(conn)

    # insert the generic subjects if they are missing
    _insert_missing_subjects(conn, species_strain_to_subject)

    # get all the existing morphologies
    rows = conn.execute(
        sa.select(
            reconstruction_morphology.c.id,
            reconstruction_morphology.c.species_id,
            reconstruction_morphology.c.strain_id,
            reconstruction_morphology.c.brain_region_id,
            reconstruction_morphology.c.license_id,
        )
    ).all()

    # insert a scientific_artifact for each model
    if rows:
        conn.execute(
            sa.insert(scientific_artifact),
            [
                {
                    "id": row.id,
                    "subject_id": species_strain_to_subject[row.species_id, row.strain_id]["id"],
                    "brain_region_id": row.brain_region_id,
                    "license_id": row.license_id,
                }
                for row in rows
            ],
        )


def _restore_data() -> None:
    conn = op.get_bind()

    # update the model from scientific_artifact and subject
    model = reconstruction_morphology
    update_values = (
        sa.select(
            model.c.id,
            scientific_artifact.c.brain_region_id,
            subject.c.species_id,
            subject.c.strain_id,
            scientific_artifact.c.license_id,
        )
        .select_from(
            model.join(
                scientific_artifact,
                scientific_artifact.c.id == model.c.id,
            ).join(
                subject,
                subject.c.id == scientific_artifact.c.subject_id,
            )
        )
        .subquery("new_values")
    )
    update_model = (
        sa.update(model)
        .values(
            brain_region_id=update_values.c.brain_region_id,
            species_id=update_values.c.species_id,
            strain_id=update_values.c.strain_id,
            license_id=update_values.c.license_id,
        )
        .where(model.c.id == update_values.c.id)
    )
    conn.execute(update_model)

    # delete scientific_artifact rows inserted during upgrade
    conn.execute(
        sa.delete(scientific_artifact).where(scientific_artifact.c.id.in_(sa.select(model.c.id)))
    )

    # delete subject and related entity rows, only for subjects with strain_id
    # that were inserted during upgrade
    species_strain_to_subject = _species_strain_to_subject(conn)
    subject_ids = [
        subject["id"]
        for (_, strain_id), subject in species_strain_to_subject.items()
        if strain_id is not None
    ]
    conn.execute(sa.delete(subject).where(subject.c.id.in_(subject_ids)))
    conn.execute(sa.delete(entity).where(entity.c.id.in_(subject_ids)))


def upgrade() -> None:
    # populate scientific_artifact
    _migrate_data()

    # create the new enums and tables
    sa.Enum(
        "electron_microscopy",
        "cell_patch",
        "fluorophore",
        name="morphologyprotocoldesign",
    ).create(op.get_bind())
    sa.Enum(
        "digital_reconstruction",
        "modified_reconstruction",
        "computationally_synthesized",
        "placeholder",
        name="morphologygenerationtype",
    ).create(op.get_bind())
    sa.Enum(
        "raw",
        "curated",
        "unraveled",
        "repaired",
        name="repairpipelinetype",
    ).create(op.get_bind())
    sa.Enum(
        "coronal",
        "sagittal",
        "horizontal",
        "custom",
        name="slicingdirectiontype",
    ).create(op.get_bind())
    sa.Enum(
        "golgi",
        "nissl",
        "luxol_fast_blue",
        "fluorescent_nissl",
        "fluorescent_dyes",
        "fluorescent_orotein_expression",
        "immunohistochemistry",
        "other",
        name="stainingtype",
    ).create(op.get_bind())
    op.create_table(
        "morphology_protocol",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("protocol_document", sa.String(), nullable=True),
        sa.Column(
            "protocol_design",
            postgresql.ENUM(
                "electron_microscopy",
                "cell_patch",
                "fluorophore",
                name="morphologyprotocoldesign",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "generation_type",
            postgresql.ENUM(
                "digital_reconstruction",
                "modified_reconstruction",
                "computationally_synthesized",
                "placeholder",
                name="morphologygenerationtype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "staining_type",
            postgresql.ENUM(
                "golgi",
                "nissl",
                "luxol_fast_blue",
                "fluorescent_nissl",
                "fluorescent_dyes",
                "fluorescent_orotein_expression",
                "immunohistochemistry",
                "other",
                name="stainingtype",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("slicing_thickness", sa.Float(), nullable=True),
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
        sa.Column("magnification", sa.Float(), nullable=True),
        sa.Column("tissue_shrinkage", sa.Float(), nullable=True),
        sa.Column("corrected_for_shrinkage", sa.Boolean(), nullable=True),
        sa.Column("method_type", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["id"], ["entity.id"], name=op.f("fk_morphology_protocol_id_entity")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_morphology_protocol")),
    )

    # drop old indexes
    op.drop_index(
        op.f("ix_reconstruction_morphology_brain_region_id"), table_name="reconstruction_morphology"
    )
    op.drop_index(
        op.f("ix_reconstruction_morphology_species_id"), table_name="reconstruction_morphology"
    )
    op.drop_index(
        op.f("ix_reconstruction_morphology_strain_id"), table_name="reconstruction_morphology"
    )
    op.drop_index(
        op.f("ix_reconstruction_morphology_license_id"), table_name="reconstruction_morphology"
    )

    # drop old constraints
    op.drop_constraint(
        op.f("fk_reconstruction_morphology_brain_region_id_brain_region"),
        "reconstruction_morphology",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_reconstruction_morphology_species_id_species"),
        "reconstruction_morphology",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_reconstruction_morphology_strain_id_species_id"),
        "reconstruction_morphology",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_reconstruction_morphology_license_id_license"),
        "reconstruction_morphology",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_reconstruction_morphology_id_entity"),
        "reconstruction_morphology",
        type_="foreignkey",
    )

    # drop old columns
    op.drop_column("reconstruction_morphology", "brain_region_id")
    op.drop_column("reconstruction_morphology", "strain_id")
    op.drop_column("reconstruction_morphology", "species_id")
    op.drop_column("reconstruction_morphology", "license_id")

    # rename table and indexes
    op.rename_table("reconstruction_morphology", "cell_morphology")
    op.execute("ALTER INDEX pk_reconstruction_morphology RENAME TO pk_cell_morphology")
    op.execute("ALTER INDEX ix_reconstruction_morphology_name RENAME TO ix_cell_morphology_name")
    op.execute(
        "ALTER INDEX ix_reconstruction_morphology_description_vector "
        "RENAME TO ix_cell_morphology_description_vector"
    )

    # rename triggers (drop and create)
    op.execute("DROP TRIGGER reconstruction_morphology_description_vector ON cell_morphology")
    op.execute(
        "CREATE TRIGGER cell_morphology_description_vector "
        "BEFORE INSERT OR UPDATE ON cell_morphology "
        "FOR EACH ROW EXECUTE FUNCTION "
        "tsvector_update_trigger('description_vector', 'pg_catalog.english', 'description', 'name')"
    )
    # rename triggers with functions
    op.execute(
        "ALTER FUNCTION unauthorized_private_reference_function_memodel_morphology_id_r() "
        "RENAME TO unauthorized_private_reference_function_memodel_morphology_id_cell_morphology"
    )
    op.execute(
        "DROP TRIGGER unauthorized_private_reference_trigger_memodel_morphology_id_re ON memodel"
    )
    op.execute(
        "CREATE TRIGGER unauthorized_private_reference_trigger_memodel_morphology_id_cell_morphology "
        "BEFORE INSERT OR UPDATE ON memodel "
        "FOR EACH ROW EXECUTE FUNCTION "
        "unauthorized_private_reference_function_memodel_morphology_id_cell_morphology()"
    )

    # add new columns
    op.add_column(
        "cell_morphology",
        sa.Column(
            "repair_pipeline_state",
            postgresql.ENUM(
                "raw",
                "curated",
                "unraveled",
                "repaired",
                name="repairpipelinetype",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "cell_morphology",
        sa.Column(
            "morphology_protocol_id",
            sa.Uuid(),
            nullable=True,
        ),
    )

    # add new foreign keys, indexes and constraints
    op.create_foreign_key(
        op.f("fk_cell_morphology_id_scientific_artifact"),
        "cell_morphology",
        "scientific_artifact",
        ["id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_cell_morphology_morphology_protocol_id_morphology_protocol"),
        "cell_morphology",
        "morphology_protocol",
        ["morphology_protocol_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_cell_morphology_morphology_protocol_id"),
        "cell_morphology",
        ["morphology_protocol_id"],
        unique=False,
    )

    # rename foreign keys in other tables
    op.execute(
        "ALTER TABLE memodel "
        "RENAME CONSTRAINT fk_memodel_morphology_id_reconstruction_morphology "
        "TO fk_memodel_morphology_id_cell_morphology"
    )
    op.execute(
        "ALTER TABLE emodel "
        "RENAME CONSTRAINT fk_emodel_exemplar_morphology_id_reconstruction_morphology "
        "TO fk_emodel_exemplar_morphology_id_cell_morphology"
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
            "electrical_cell_recording",
            "electrical_recording_stimulus",
            "emodel",
            "experimental_bouton_density",
            "experimental_neuron_density",
            "experimental_synapses_per_connection",
            "external_url",
            "ion_channel_model",
            "memodel",
            "mesh",
            "memodel_calibration_result",
            "me_type_density",
            "morphology_protocol",
            "publication",
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
        enum_values_to_rename=[
            ("reconstruction_morphology", "cell_morphology"),
        ],
    )
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


def downgrade() -> None:
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
            "external_url",
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
        enum_values_to_rename=[
            ("cell_morphology", "reconstruction_morphology"),
        ],
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

    # drop old constraints
    op.drop_constraint(
        op.f("fk_cell_morphology_morphology_protocol_id_morphology_protocol"),
        "cell_morphology",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_cell_morphology_id_scientific_artifact"),
        "cell_morphology",
        type_="foreignkey",
    )

    # drop old columns
    op.drop_column("cell_morphology", "repair_pipeline_state")
    op.drop_column("cell_morphology", "morphology_protocol_id")

    # rename table and indexes
    op.rename_table("cell_morphology", "reconstruction_morphology")
    op.execute("ALTER INDEX pk_cell_morphology RENAME TO pk_reconstruction_morphology")
    op.execute("ALTER INDEX ix_cell_morphology_name RENAME TO ix_reconstruction_morphology_name")
    op.execute(
        "ALTER INDEX ix_cell_morphology_description_vector "
        "RENAME TO ix_reconstruction_morphology_description_vector"
    )

    # rename triggers (drop and create)
    op.execute("DROP TRIGGER cell_morphology_description_vector ON reconstruction_morphology")
    op.execute(
        "CREATE TRIGGER reconstruction_morphology_description_vector "
        "BEFORE INSERT OR UPDATE ON reconstruction_morphology "
        "FOR EACH ROW EXECUTE FUNCTION "
        "tsvector_update_trigger('description_vector', 'pg_catalog.english', 'description', 'name')"
    )
    # rename triggers with functions
    op.execute(
        "ALTER FUNCTION unauthorized_private_reference_function_memodel_morphology_id_cell_morphology() "
        "RENAME TO unauthorized_private_reference_function_memodel_morphology_id_r"
    )
    op.execute(
        "DROP TRIGGER unauthorized_private_reference_trigger_memodel_morphology_id_cell_morphology ON memodel"
    )
    op.execute(
        "CREATE TRIGGER unauthorized_private_reference_trigger_memodel_morphology_id_re "
        "BEFORE INSERT OR UPDATE ON memodel "
        "FOR EACH ROW EXECUTE FUNCTION "
        "unauthorized_private_reference_function_memodel_morphology_id_r()"
    )

    # add columns
    op.add_column(
        "reconstruction_morphology",
        sa.Column("brain_region_id", sa.UUID(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "reconstruction_morphology",
        sa.Column("species_id", sa.UUID(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "reconstruction_morphology",
        sa.Column("strain_id", sa.UUID(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "reconstruction_morphology",
        sa.Column("license_id", sa.UUID(), autoincrement=False, nullable=True),
    )

    # create foreign keys
    op.create_foreign_key(
        op.f("fk_reconstruction_morphology_id_entity"),
        "reconstruction_morphology",
        "entity",
        ["id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_reconstruction_morphology_brain_region_id_brain_region"),
        "reconstruction_morphology",
        "brain_region",
        ["brain_region_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_reconstruction_morphology_species_id_species"),
        "reconstruction_morphology",
        "species",
        ["species_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_reconstruction_morphology_strain_id_species_id"),
        "reconstruction_morphology",
        "strain",
        ["strain_id", "species_id"],
        ["id", "species_id"],
    )
    op.create_foreign_key(
        op.f("fk_reconstruction_morphology_license_id_license"),
        "reconstruction_morphology",
        "license",
        ["license_id"],
        ["id"],
    )

    # create indexes
    op.create_index(
        op.f("ix_reconstruction_morphology_brain_region_id"),
        "reconstruction_morphology",
        ["brain_region_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reconstruction_morphology_species_id"),
        "reconstruction_morphology",
        ["species_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reconstruction_morphology_strain_id"),
        "reconstruction_morphology",
        ["strain_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reconstruction_morphology_license_id"),
        "reconstruction_morphology",
        ["license_id"],
        unique=False,
    )

    # rename foreign keys in other tables
    op.execute(
        "ALTER TABLE memodel "
        "RENAME CONSTRAINT fk_memodel_morphology_id_cell_morphology "
        "TO fk_memodel_morphology_id_reconstruction_morphology"
    )
    op.execute(
        "ALTER TABLE emodel "
        "RENAME CONSTRAINT fk_emodel_exemplar_morphology_id_cell_morphology "
        "TO fk_emodel_exemplar_morphology_id_reconstruction_morphology"
    )

    # drop other constraints, tables, and enums
    op.drop_constraint(
        op.f("fk_morphology_protocol_id_entity"),
        "morphology_protocol",
        type_="foreignkey",
    )
    op.drop_table("morphology_protocol")
    sa.Enum(
        "golgi",
        "nissl",
        "luxol_fast_blue",
        "fluorescent_nissl",
        "fluorescent_dyes",
        "fluorescent_orotein_expression",
        "immunohistochemistry",
        "other",
        name="stainingtype",
    ).drop(op.get_bind())
    sa.Enum(
        "coronal",
        "sagittal",
        "horizontal",
        "custom",
        name="slicingdirectiontype",
    ).drop(op.get_bind())
    sa.Enum(
        "raw",
        "curated",
        "unraveled",
        "repaired",
        name="repairpipelinetype",
    ).drop(op.get_bind())
    sa.Enum(
        "digital_reconstruction",
        "modified_reconstruction",
        "computationally_synthesized",
        "placeholder",
        name="morphologygenerationtype",
    ).drop(op.get_bind())
    sa.Enum(
        "electron_microscopy",
        "cell_patch",
        "fluorophore",
        name="morphologyprotocoldesign",
    ).drop(op.get_bind())

    # restore the previous data
    _restore_data()

    # make brain_region_id non-nullable after update
    op.alter_column(
        "reconstruction_morphology",
        "brain_region_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
    # make species_id non-nullable after update
    op.alter_column(
        "reconstruction_morphology",
        "species_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
