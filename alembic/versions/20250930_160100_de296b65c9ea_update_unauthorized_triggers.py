"""Update unauthorized triggers

Revision ID: de296b65c9ea
Revises: 877ef8817d43
Create Date: 2025-09-30 16:01:00.611255

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic_utils.pg_function import PGFunction
from sqlalchemy import text as sql_text
from alembic_utils.pg_trigger import PGTrigger
from sqlalchemy import text as sql_text

from sqlalchemy import Text
import app.db.types

# revision identifiers, used by Alembic.
revision: str = "de296b65c9ea"
down_revision: Union[str, None] = "877ef8817d43"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # create new functions

    public_auth_fn_brain_atlas_region_brain_atlas_id = PGFunction(
        schema="public",
        signature="auth_fn_brain_atlas_region_brain_atlas_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.brain_atlas_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_brain_atlas_region_brain_atlas_id)

    public_auth_fn_cell_morphology_cell_morphology_protocol_id = PGFunction(
        schema="public",
        signature="auth_fn_cell_morphology_cell_morphology_protocol_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                IF NEW.cell_morphology_protocol_id IS NULL THEN RETURN NEW; END IF;\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.cell_morphology_protocol_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_cell_morphology_cell_morphology_protocol_id)

    public_auth_fn_circuit_atlas_id = PGFunction(
        schema="public",
        signature="auth_fn_circuit_atlas_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                IF NEW.atlas_id IS NULL THEN RETURN NEW; END IF;\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.atlas_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_circuit_atlas_id)

    public_auth_fn_circuit_root_circuit_id = PGFunction(
        schema="public",
        signature="auth_fn_circuit_root_circuit_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                IF NEW.root_circuit_id IS NULL THEN RETURN NEW; END IF;\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.root_circuit_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_circuit_root_circuit_id)

    public_auth_fn_electrical_recording_stimulus_recording_id = PGFunction(
        schema="public",
        signature="auth_fn_electrical_recording_stimulus_recording_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.recording_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_electrical_recording_stimulus_recording_id)

    public_auth_fn_em_cell_mesh_em_dense_reconstruction_dataset_id = PGFunction(
        schema="public",
        signature="auth_fn_em_cell_mesh_em_dense_reconstruction_dataset_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.em_dense_reconstruction_dataset_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_em_cell_mesh_em_dense_reconstruction_dataset_id)

    public_auth_fn_emodel_exemplar_morphology_id = PGFunction(
        schema="public",
        signature="auth_fn_emodel_exemplar_morphology_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.exemplar_morphology_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_emodel_exemplar_morphology_id)

    public_auth_fn_experimental_bouton_density_subject_id = PGFunction(
        schema="public",
        signature="auth_fn_experimental_bouton_density_subject_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                IF NEW.subject_id IS NULL THEN RETURN NEW; END IF;\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.subject_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_experimental_bouton_density_subject_id)

    public_auth_fn_experimental_neuron_density_subject_id = PGFunction(
        schema="public",
        signature="auth_fn_experimental_neuron_density_subject_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                IF NEW.subject_id IS NULL THEN RETURN NEW; END IF;\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.subject_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_experimental_neuron_density_subject_id)

    public_auth_fn_experimental_synapses_per_connection_subject_id = PGFunction(
        schema="public",
        signature="auth_fn_experimental_synapses_per_connection_subject_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                IF NEW.subject_id IS NULL THEN RETURN NEW; END IF;\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.subject_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_experimental_synapses_per_connection_subject_id)

    public_auth_fn_memodel_emodel_id = PGFunction(
        schema="public",
        signature="auth_fn_memodel_emodel_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.emodel_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_memodel_emodel_id)

    public_auth_fn_memodel_morphology_id = PGFunction(
        schema="public",
        signature="auth_fn_memodel_morphology_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.morphology_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_memodel_morphology_id)

    public_auth_fn_memodel_calibration_result_calibrated_entity_id = PGFunction(
        schema="public",
        signature="auth_fn_memodel_calibration_result_calibrated_entity_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.calibrated_entity_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_memodel_calibration_result_calibrated_entity_id)

    public_auth_fn_scientific_artifact_subject_id = PGFunction(
        schema="public",
        signature="auth_fn_scientific_artifact_subject_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                IF NEW.subject_id IS NULL THEN RETURN NEW; END IF;\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.subject_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_scientific_artifact_subject_id)

    public_auth_fn_simulation_entity_id = PGFunction(
        schema="public",
        signature="auth_fn_simulation_entity_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.entity_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_simulation_entity_id)

    public_auth_fn_simulation_simulation_campaign_id = PGFunction(
        schema="public",
        signature="auth_fn_simulation_simulation_campaign_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.simulation_campaign_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_simulation_simulation_campaign_id)

    public_auth_fn_simulation_campaign_entity_id = PGFunction(
        schema="public",
        signature="auth_fn_simulation_campaign_entity_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.entity_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_simulation_campaign_entity_id)

    public_auth_fn_simulation_result_simulation_id = PGFunction(
        schema="public",
        signature="auth_fn_simulation_result_simulation_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.simulation_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_simulation_result_simulation_id)

    public_auth_fn_single_neuron_simulation_me_model_id = PGFunction(
        schema="public",
        signature="auth_fn_single_neuron_simulation_me_model_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.me_model_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_single_neuron_simulation_me_model_id)

    public_auth_fn_single_neuron_synaptome_me_model_id = PGFunction(
        schema="public",
        signature="auth_fn_single_neuron_synaptome_me_model_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.me_model_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_single_neuron_synaptome_me_model_id)

    public_auth_fn_single_neuron_synaptome_simulation_synaptome_id = PGFunction(
        schema="public",
        signature="auth_fn_single_neuron_synaptome_simulation_synaptome_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.synaptome_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_single_neuron_synaptome_simulation_synaptome_id)

    public_auth_fn_validation_result_validated_entity_id = PGFunction(
        schema="public",
        signature="auth_fn_validation_result_validated_entity_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.validated_entity_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.create_entity(public_auth_fn_validation_result_validated_entity_id)

    public_brain_atlas_region_auth_trg_brain_atlas_region_brain_atlas_id = PGTrigger(
        schema="public",
        signature="auth_trg_brain_atlas_region_brain_atlas_id",
        on_entity="public.brain_atlas_region",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON brain_atlas_region\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_brain_atlas_region_brain_atlas_id()",
    )
    op.create_entity(public_brain_atlas_region_auth_trg_brain_atlas_region_brain_atlas_id)

    # create new triggers

    public_cell_morphology_auth_trg_cell_morphology_cell_morphology_protocol_id = PGTrigger(
        schema="public",
        signature="auth_trg_cell_morphology_cell_morphology_protocol_id",
        on_entity="public.cell_morphology",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON cell_morphology\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_cell_morphology_cell_morphology_protocol_id()",
    )
    op.create_entity(public_cell_morphology_auth_trg_cell_morphology_cell_morphology_protocol_id)

    public_circuit_auth_trg_circuit_atlas_id = PGTrigger(
        schema="public",
        signature="auth_trg_circuit_atlas_id",
        on_entity="public.circuit",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON circuit\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_circuit_atlas_id()",
    )
    op.create_entity(public_circuit_auth_trg_circuit_atlas_id)

    public_circuit_auth_trg_circuit_root_circuit_id = PGTrigger(
        schema="public",
        signature="auth_trg_circuit_root_circuit_id",
        on_entity="public.circuit",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON circuit\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_circuit_root_circuit_id()",
    )
    op.create_entity(public_circuit_auth_trg_circuit_root_circuit_id)

    public_electrical_recording_stimulus_auth_trg_electrical_recording_stimulus_recording_id = PGTrigger(
        schema="public",
        signature="auth_trg_electrical_recording_stimulus_recording_id",
        on_entity="public.electrical_recording_stimulus",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON electrical_recording_stimulus\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_electrical_recording_stimulus_recording_id()",
    )
    op.create_entity(
        public_electrical_recording_stimulus_auth_trg_electrical_recording_stimulus_recording_id
    )

    public_em_cell_mesh_auth_trg_em_cell_mesh_em_dense_reconstruction_dataset_id = PGTrigger(
        schema="public",
        signature="auth_trg_em_cell_mesh_em_dense_reconstruction_dataset_id",
        on_entity="public.em_cell_mesh",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON em_cell_mesh\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_em_cell_mesh_em_dense_reconstruction_dataset_id()",
    )
    op.create_entity(public_em_cell_mesh_auth_trg_em_cell_mesh_em_dense_reconstruction_dataset_id)

    public_emodel_auth_trg_emodel_exemplar_morphology_id = PGTrigger(
        schema="public",
        signature="auth_trg_emodel_exemplar_morphology_id",
        on_entity="public.emodel",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON emodel\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_emodel_exemplar_morphology_id()",
    )
    op.create_entity(public_emodel_auth_trg_emodel_exemplar_morphology_id)

    public_experimental_bouton_density_auth_trg_experimental_bouton_density_subject_id = PGTrigger(
        schema="public",
        signature="auth_trg_experimental_bouton_density_subject_id",
        on_entity="public.experimental_bouton_density",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON experimental_bouton_density\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_experimental_bouton_density_subject_id()",
    )
    op.create_entity(
        public_experimental_bouton_density_auth_trg_experimental_bouton_density_subject_id
    )

    public_experimental_neuron_density_auth_trg_experimental_neuron_density_subject_id = PGTrigger(
        schema="public",
        signature="auth_trg_experimental_neuron_density_subject_id",
        on_entity="public.experimental_neuron_density",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON experimental_neuron_density\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_experimental_neuron_density_subject_id()",
    )
    op.create_entity(
        public_experimental_neuron_density_auth_trg_experimental_neuron_density_subject_id
    )

    public_experimental_synapses_per_connection_auth_trg_experimental_synapses_per_connection_subject_id = PGTrigger(
        schema="public",
        signature="auth_trg_experimental_synapses_per_connection_subject_id",
        on_entity="public.experimental_synapses_per_connection",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON experimental_synapses_per_connection\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_experimental_synapses_per_connection_subject_id()",
    )
    op.create_entity(
        public_experimental_synapses_per_connection_auth_trg_experimental_synapses_per_connection_subject_id
    )

    public_memodel_auth_trg_memodel_emodel_id = PGTrigger(
        schema="public",
        signature="auth_trg_memodel_emodel_id",
        on_entity="public.memodel",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON memodel\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_memodel_emodel_id()",
    )
    op.create_entity(public_memodel_auth_trg_memodel_emodel_id)

    public_memodel_auth_trg_memodel_morphology_id = PGTrigger(
        schema="public",
        signature="auth_trg_memodel_morphology_id",
        on_entity="public.memodel",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON memodel\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_memodel_morphology_id()",
    )
    op.create_entity(public_memodel_auth_trg_memodel_morphology_id)

    public_memodel_calibration_result_auth_trg_memodel_calibration_result_calibrated_entity_id = PGTrigger(
        schema="public",
        signature="auth_trg_memodel_calibration_result_calibrated_entity_id",
        on_entity="public.memodel_calibration_result",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON memodel_calibration_result\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_memodel_calibration_result_calibrated_entity_id()",
    )
    op.create_entity(
        public_memodel_calibration_result_auth_trg_memodel_calibration_result_calibrated_entity_id
    )

    public_scientific_artifact_auth_trg_scientific_artifact_subject_id = PGTrigger(
        schema="public",
        signature="auth_trg_scientific_artifact_subject_id",
        on_entity="public.scientific_artifact",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON scientific_artifact\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_scientific_artifact_subject_id()",
    )
    op.create_entity(public_scientific_artifact_auth_trg_scientific_artifact_subject_id)

    public_simulation_auth_trg_simulation_entity_id = PGTrigger(
        schema="public",
        signature="auth_trg_simulation_entity_id",
        on_entity="public.simulation",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON simulation\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_simulation_entity_id()",
    )
    op.create_entity(public_simulation_auth_trg_simulation_entity_id)

    public_simulation_auth_trg_simulation_simulation_campaign_id = PGTrigger(
        schema="public",
        signature="auth_trg_simulation_simulation_campaign_id",
        on_entity="public.simulation",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON simulation\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_simulation_simulation_campaign_id()",
    )
    op.create_entity(public_simulation_auth_trg_simulation_simulation_campaign_id)

    public_simulation_campaign_auth_trg_simulation_campaign_entity_id = PGTrigger(
        schema="public",
        signature="auth_trg_simulation_campaign_entity_id",
        on_entity="public.simulation_campaign",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON simulation_campaign\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_simulation_campaign_entity_id()",
    )
    op.create_entity(public_simulation_campaign_auth_trg_simulation_campaign_entity_id)

    public_simulation_result_auth_trg_simulation_result_simulation_id = PGTrigger(
        schema="public",
        signature="auth_trg_simulation_result_simulation_id",
        on_entity="public.simulation_result",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON simulation_result\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_simulation_result_simulation_id()",
    )
    op.create_entity(public_simulation_result_auth_trg_simulation_result_simulation_id)

    public_single_neuron_simulation_auth_trg_single_neuron_simulation_me_model_id = PGTrigger(
        schema="public",
        signature="auth_trg_single_neuron_simulation_me_model_id",
        on_entity="public.single_neuron_simulation",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON single_neuron_simulation\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_single_neuron_simulation_me_model_id()",
    )
    op.create_entity(public_single_neuron_simulation_auth_trg_single_neuron_simulation_me_model_id)

    public_single_neuron_synaptome_auth_trg_single_neuron_synaptome_me_model_id = PGTrigger(
        schema="public",
        signature="auth_trg_single_neuron_synaptome_me_model_id",
        on_entity="public.single_neuron_synaptome",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON single_neuron_synaptome\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_single_neuron_synaptome_me_model_id()",
    )
    op.create_entity(public_single_neuron_synaptome_auth_trg_single_neuron_synaptome_me_model_id)

    public_single_neuron_synaptome_simulation_auth_trg_single_neuron_synaptome_simulation_synaptome_id = PGTrigger(
        schema="public",
        signature="auth_trg_single_neuron_synaptome_simulation_synaptome_id",
        on_entity="public.single_neuron_synaptome_simulation",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON single_neuron_synaptome_simulation\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_single_neuron_synaptome_simulation_synaptome_id()",
    )
    op.create_entity(
        public_single_neuron_synaptome_simulation_auth_trg_single_neuron_synaptome_simulation_synaptome_id
    )

    public_validation_result_auth_trg_validation_result_validated_entity_id = PGTrigger(
        schema="public",
        signature="auth_trg_validation_result_validated_entity_id",
        on_entity="public.validation_result",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON validation_result\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_validation_result_validated_entity_id()",
    )
    op.create_entity(public_validation_result_auth_trg_validation_result_validated_entity_id)

    # drop old triggers

    public_emodel_unauthorized_private_reference_trigger_emodel_exemplar_morpholo = PGTrigger(
        schema="public",
        signature="unauthorized_private_reference_trigger_emodel_exemplar_morpholo",
        on_entity="public.emodel",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON public.emodel FOR EACH ROW EXECUTE FUNCTION unauthorized_private_reference_function_emodel_exemplar_morphol()",
    )
    op.drop_entity(public_emodel_unauthorized_private_reference_trigger_emodel_exemplar_morpholo)

    public_memodel_unauthorized_private_reference_trigger_memodel_emodel_id_emodel = PGTrigger(
        schema="public",
        signature="unauthorized_private_reference_trigger_memodel_emodel_id_emodel",
        on_entity="public.memodel",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON public.memodel FOR EACH ROW EXECUTE FUNCTION unauthorized_private_reference_function_memodel_emodel_id_emode()",
    )
    op.drop_entity(public_memodel_unauthorized_private_reference_trigger_memodel_emodel_id_emodel)

    public_memodel_unauthorized_private_reference_trigger_memodel_morphology_id_ce = PGTrigger(
        schema="public",
        signature="unauthorized_private_reference_trigger_memodel_morphology_id_ce",
        on_entity="public.memodel",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON public.memodel FOR EACH ROW EXECUTE FUNCTION unauthorized_private_reference_function_memodel_morphology_id_c()",
    )
    op.drop_entity(public_memodel_unauthorized_private_reference_trigger_memodel_morphology_id_ce)

    public_cell_morphology_unauthorized_private_reference_trigger_cell_morphology_cell_mor = PGTrigger(
        schema="public",
        signature="unauthorized_private_reference_trigger_cell_morphology_cell_mor",
        on_entity="public.cell_morphology",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON public.cell_morphology FOR EACH ROW EXECUTE FUNCTION unauthorized_private_reference_function_cell_morphology_cell_mo()",
    )
    op.drop_entity(
        public_cell_morphology_unauthorized_private_reference_trigger_cell_morphology_cell_mor
    )

    # drop old functions

    public_unauthorized_private_reference_function_emodel_exemplar_morphol = PGFunction(
        schema="public",
        signature="unauthorized_private_reference_function_emodel_exemplar_morphol()",
        definition="returns trigger\n LANGUAGE plpgsql\nAS $function$\n            BEGIN\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.exemplar_morphology_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $function$",
    )
    op.drop_entity(public_unauthorized_private_reference_function_emodel_exemplar_morphol)

    public_unauthorized_private_reference_function_memodel_emodel_id_emode = PGFunction(
        schema="public",
        signature="unauthorized_private_reference_function_memodel_emodel_id_emode()",
        definition="returns trigger\n LANGUAGE plpgsql\nAS $function$\n            BEGIN\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.emodel_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $function$",
    )
    op.drop_entity(public_unauthorized_private_reference_function_memodel_emodel_id_emode)

    public_unauthorized_private_reference_function_memodel_morphology_id_c = PGFunction(
        schema="public",
        signature="unauthorized_private_reference_function_memodel_morphology_id_c()",
        definition="returns trigger\n LANGUAGE plpgsql\nAS $function$\n            BEGIN\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.morphology_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $function$",
    )
    op.drop_entity(public_unauthorized_private_reference_function_memodel_morphology_id_c)

    public_unauthorized_private_reference_function_cell_morphology_cell_mo = PGFunction(
        schema="public",
        signature="unauthorized_private_reference_function_cell_morphology_cell_mo()",
        definition="returns trigger\n LANGUAGE plpgsql\nAS $function$\n            BEGIN\n                IF NEW.cell_morphology_protocol_id IS NULL THEN RETURN NEW; END IF;\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.cell_morphology_protocol_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $function$",
    )
    op.drop_entity(public_unauthorized_private_reference_function_cell_morphology_cell_mo)


def downgrade() -> None:
    # restore old functions

    public_unauthorized_private_reference_function_cell_morphology_cell_mo = PGFunction(
        schema="public",
        signature="unauthorized_private_reference_function_cell_morphology_cell_mo()",
        definition="returns trigger\n LANGUAGE plpgsql\nAS $function$\n            BEGIN\n                IF NEW.cell_morphology_protocol_id IS NULL THEN RETURN NEW; END IF;\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.cell_morphology_protocol_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $function$",
    )
    op.create_entity(public_unauthorized_private_reference_function_cell_morphology_cell_mo)

    public_unauthorized_private_reference_function_memodel_morphology_id_c = PGFunction(
        schema="public",
        signature="unauthorized_private_reference_function_memodel_morphology_id_c()",
        definition="returns trigger\n LANGUAGE plpgsql\nAS $function$\n            BEGIN\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.morphology_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $function$",
    )
    op.create_entity(public_unauthorized_private_reference_function_memodel_morphology_id_c)

    public_unauthorized_private_reference_function_memodel_emodel_id_emode = PGFunction(
        schema="public",
        signature="unauthorized_private_reference_function_memodel_emodel_id_emode()",
        definition="returns trigger\n LANGUAGE plpgsql\nAS $function$\n            BEGIN\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.emodel_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $function$",
    )
    op.create_entity(public_unauthorized_private_reference_function_memodel_emodel_id_emode)

    public_unauthorized_private_reference_function_emodel_exemplar_morphol = PGFunction(
        schema="public",
        signature="unauthorized_private_reference_function_emodel_exemplar_morphol()",
        definition="returns trigger\n LANGUAGE plpgsql\nAS $function$\n            BEGIN\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.exemplar_morphology_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $function$",
    )
    op.create_entity(public_unauthorized_private_reference_function_emodel_exemplar_morphol)

    # restore old triggers

    public_cell_morphology_unauthorized_private_reference_trigger_cell_morphology_cell_mor = PGTrigger(
        schema="public",
        signature="unauthorized_private_reference_trigger_cell_morphology_cell_mor",
        on_entity="public.cell_morphology",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON public.cell_morphology FOR EACH ROW EXECUTE FUNCTION unauthorized_private_reference_function_cell_morphology_cell_mo()",
    )
    op.create_entity(
        public_cell_morphology_unauthorized_private_reference_trigger_cell_morphology_cell_mor
    )

    public_memodel_unauthorized_private_reference_trigger_memodel_morphology_id_ce = PGTrigger(
        schema="public",
        signature="unauthorized_private_reference_trigger_memodel_morphology_id_ce",
        on_entity="public.memodel",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON public.memodel FOR EACH ROW EXECUTE FUNCTION unauthorized_private_reference_function_memodel_morphology_id_c()",
    )
    op.create_entity(public_memodel_unauthorized_private_reference_trigger_memodel_morphology_id_ce)

    public_memodel_unauthorized_private_reference_trigger_memodel_emodel_id_emodel = PGTrigger(
        schema="public",
        signature="unauthorized_private_reference_trigger_memodel_emodel_id_emodel",
        on_entity="public.memodel",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON public.memodel FOR EACH ROW EXECUTE FUNCTION unauthorized_private_reference_function_memodel_emodel_id_emode()",
    )
    op.create_entity(public_memodel_unauthorized_private_reference_trigger_memodel_emodel_id_emodel)

    public_emodel_unauthorized_private_reference_trigger_emodel_exemplar_morpholo = PGTrigger(
        schema="public",
        signature="unauthorized_private_reference_trigger_emodel_exemplar_morpholo",
        on_entity="public.emodel",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON public.emodel FOR EACH ROW EXECUTE FUNCTION unauthorized_private_reference_function_emodel_exemplar_morphol()",
    )
    op.create_entity(public_emodel_unauthorized_private_reference_trigger_emodel_exemplar_morpholo)

    # drop new triggers

    public_validation_result_auth_trg_validation_result_validated_entity_id = PGTrigger(
        schema="public",
        signature="auth_trg_validation_result_validated_entity_id",
        on_entity="public.validation_result",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON validation_result\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_validation_result_validated_entity_id()",
    )
    op.drop_entity(public_validation_result_auth_trg_validation_result_validated_entity_id)

    public_single_neuron_synaptome_simulation_auth_trg_single_neuron_synaptome_simulation_synaptome_id = PGTrigger(
        schema="public",
        signature="auth_trg_single_neuron_synaptome_simulation_synaptome_id",
        on_entity="public.single_neuron_synaptome_simulation",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON single_neuron_synaptome_simulation\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_single_neuron_synaptome_simulation_synaptome_id()",
    )
    op.drop_entity(
        public_single_neuron_synaptome_simulation_auth_trg_single_neuron_synaptome_simulation_synaptome_id
    )

    public_single_neuron_synaptome_auth_trg_single_neuron_synaptome_me_model_id = PGTrigger(
        schema="public",
        signature="auth_trg_single_neuron_synaptome_me_model_id",
        on_entity="public.single_neuron_synaptome",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON single_neuron_synaptome\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_single_neuron_synaptome_me_model_id()",
    )
    op.drop_entity(public_single_neuron_synaptome_auth_trg_single_neuron_synaptome_me_model_id)

    public_single_neuron_simulation_auth_trg_single_neuron_simulation_me_model_id = PGTrigger(
        schema="public",
        signature="auth_trg_single_neuron_simulation_me_model_id",
        on_entity="public.single_neuron_simulation",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON single_neuron_simulation\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_single_neuron_simulation_me_model_id()",
    )
    op.drop_entity(public_single_neuron_simulation_auth_trg_single_neuron_simulation_me_model_id)

    public_simulation_result_auth_trg_simulation_result_simulation_id = PGTrigger(
        schema="public",
        signature="auth_trg_simulation_result_simulation_id",
        on_entity="public.simulation_result",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON simulation_result\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_simulation_result_simulation_id()",
    )
    op.drop_entity(public_simulation_result_auth_trg_simulation_result_simulation_id)

    public_simulation_campaign_auth_trg_simulation_campaign_entity_id = PGTrigger(
        schema="public",
        signature="auth_trg_simulation_campaign_entity_id",
        on_entity="public.simulation_campaign",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON simulation_campaign\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_simulation_campaign_entity_id()",
    )
    op.drop_entity(public_simulation_campaign_auth_trg_simulation_campaign_entity_id)

    public_simulation_auth_trg_simulation_simulation_campaign_id = PGTrigger(
        schema="public",
        signature="auth_trg_simulation_simulation_campaign_id",
        on_entity="public.simulation",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON simulation\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_simulation_simulation_campaign_id()",
    )
    op.drop_entity(public_simulation_auth_trg_simulation_simulation_campaign_id)

    public_simulation_auth_trg_simulation_entity_id = PGTrigger(
        schema="public",
        signature="auth_trg_simulation_entity_id",
        on_entity="public.simulation",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON simulation\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_simulation_entity_id()",
    )
    op.drop_entity(public_simulation_auth_trg_simulation_entity_id)

    public_scientific_artifact_auth_trg_scientific_artifact_subject_id = PGTrigger(
        schema="public",
        signature="auth_trg_scientific_artifact_subject_id",
        on_entity="public.scientific_artifact",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON scientific_artifact\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_scientific_artifact_subject_id()",
    )
    op.drop_entity(public_scientific_artifact_auth_trg_scientific_artifact_subject_id)

    public_memodel_calibration_result_auth_trg_memodel_calibration_result_calibrated_entity_id = PGTrigger(
        schema="public",
        signature="auth_trg_memodel_calibration_result_calibrated_entity_id",
        on_entity="public.memodel_calibration_result",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON memodel_calibration_result\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_memodel_calibration_result_calibrated_entity_id()",
    )
    op.drop_entity(
        public_memodel_calibration_result_auth_trg_memodel_calibration_result_calibrated_entity_id
    )

    public_memodel_auth_trg_memodel_morphology_id = PGTrigger(
        schema="public",
        signature="auth_trg_memodel_morphology_id",
        on_entity="public.memodel",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON memodel\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_memodel_morphology_id()",
    )
    op.drop_entity(public_memodel_auth_trg_memodel_morphology_id)

    public_memodel_auth_trg_memodel_emodel_id = PGTrigger(
        schema="public",
        signature="auth_trg_memodel_emodel_id",
        on_entity="public.memodel",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON memodel\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_memodel_emodel_id()",
    )
    op.drop_entity(public_memodel_auth_trg_memodel_emodel_id)

    public_experimental_synapses_per_connection_auth_trg_experimental_synapses_per_connection_subject_id = PGTrigger(
        schema="public",
        signature="auth_trg_experimental_synapses_per_connection_subject_id",
        on_entity="public.experimental_synapses_per_connection",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON experimental_synapses_per_connection\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_experimental_synapses_per_connection_subject_id()",
    )
    op.drop_entity(
        public_experimental_synapses_per_connection_auth_trg_experimental_synapses_per_connection_subject_id
    )

    public_experimental_neuron_density_auth_trg_experimental_neuron_density_subject_id = PGTrigger(
        schema="public",
        signature="auth_trg_experimental_neuron_density_subject_id",
        on_entity="public.experimental_neuron_density",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON experimental_neuron_density\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_experimental_neuron_density_subject_id()",
    )
    op.drop_entity(
        public_experimental_neuron_density_auth_trg_experimental_neuron_density_subject_id
    )

    public_experimental_bouton_density_auth_trg_experimental_bouton_density_subject_id = PGTrigger(
        schema="public",
        signature="auth_trg_experimental_bouton_density_subject_id",
        on_entity="public.experimental_bouton_density",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON experimental_bouton_density\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_experimental_bouton_density_subject_id()",
    )
    op.drop_entity(
        public_experimental_bouton_density_auth_trg_experimental_bouton_density_subject_id
    )

    public_emodel_auth_trg_emodel_exemplar_morphology_id = PGTrigger(
        schema="public",
        signature="auth_trg_emodel_exemplar_morphology_id",
        on_entity="public.emodel",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON emodel\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_emodel_exemplar_morphology_id()",
    )
    op.drop_entity(public_emodel_auth_trg_emodel_exemplar_morphology_id)

    public_em_cell_mesh_auth_trg_em_cell_mesh_em_dense_reconstruction_dataset_id = PGTrigger(
        schema="public",
        signature="auth_trg_em_cell_mesh_em_dense_reconstruction_dataset_id",
        on_entity="public.em_cell_mesh",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON em_cell_mesh\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_em_cell_mesh_em_dense_reconstruction_dataset_id()",
    )
    op.drop_entity(public_em_cell_mesh_auth_trg_em_cell_mesh_em_dense_reconstruction_dataset_id)

    public_electrical_recording_stimulus_auth_trg_electrical_recording_stimulus_recording_id = PGTrigger(
        schema="public",
        signature="auth_trg_electrical_recording_stimulus_recording_id",
        on_entity="public.electrical_recording_stimulus",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON electrical_recording_stimulus\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_electrical_recording_stimulus_recording_id()",
    )
    op.drop_entity(
        public_electrical_recording_stimulus_auth_trg_electrical_recording_stimulus_recording_id
    )

    public_circuit_auth_trg_circuit_root_circuit_id = PGTrigger(
        schema="public",
        signature="auth_trg_circuit_root_circuit_id",
        on_entity="public.circuit",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON circuit\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_circuit_root_circuit_id()",
    )
    op.drop_entity(public_circuit_auth_trg_circuit_root_circuit_id)

    public_circuit_auth_trg_circuit_atlas_id = PGTrigger(
        schema="public",
        signature="auth_trg_circuit_atlas_id",
        on_entity="public.circuit",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON circuit\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_circuit_atlas_id()",
    )
    op.drop_entity(public_circuit_auth_trg_circuit_atlas_id)

    public_cell_morphology_auth_trg_cell_morphology_cell_morphology_protocol_id = PGTrigger(
        schema="public",
        signature="auth_trg_cell_morphology_cell_morphology_protocol_id",
        on_entity="public.cell_morphology",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON cell_morphology\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_cell_morphology_cell_morphology_protocol_id()",
    )
    op.drop_entity(public_cell_morphology_auth_trg_cell_morphology_cell_morphology_protocol_id)

    public_brain_atlas_region_auth_trg_brain_atlas_region_brain_atlas_id = PGTrigger(
        schema="public",
        signature="auth_trg_brain_atlas_region_brain_atlas_id",
        on_entity="public.brain_atlas_region",
        is_constraint=False,
        definition="BEFORE INSERT OR UPDATE ON brain_atlas_region\n            FOR EACH ROW EXECUTE FUNCTION auth_fn_brain_atlas_region_brain_atlas_id()",
    )
    op.drop_entity(public_brain_atlas_region_auth_trg_brain_atlas_region_brain_atlas_id)

    # drop new functions

    public_auth_fn_validation_result_validated_entity_id = PGFunction(
        schema="public",
        signature="auth_fn_validation_result_validated_entity_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.validated_entity_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_validation_result_validated_entity_id)

    public_auth_fn_single_neuron_synaptome_simulation_synaptome_id = PGFunction(
        schema="public",
        signature="auth_fn_single_neuron_synaptome_simulation_synaptome_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.synaptome_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_single_neuron_synaptome_simulation_synaptome_id)

    public_auth_fn_single_neuron_synaptome_me_model_id = PGFunction(
        schema="public",
        signature="auth_fn_single_neuron_synaptome_me_model_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.me_model_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_single_neuron_synaptome_me_model_id)

    public_auth_fn_single_neuron_simulation_me_model_id = PGFunction(
        schema="public",
        signature="auth_fn_single_neuron_simulation_me_model_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.me_model_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_single_neuron_simulation_me_model_id)

    public_auth_fn_simulation_result_simulation_id = PGFunction(
        schema="public",
        signature="auth_fn_simulation_result_simulation_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.simulation_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_simulation_result_simulation_id)

    public_auth_fn_simulation_campaign_entity_id = PGFunction(
        schema="public",
        signature="auth_fn_simulation_campaign_entity_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.entity_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_simulation_campaign_entity_id)

    public_auth_fn_simulation_simulation_campaign_id = PGFunction(
        schema="public",
        signature="auth_fn_simulation_simulation_campaign_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.simulation_campaign_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_simulation_simulation_campaign_id)

    public_auth_fn_simulation_entity_id = PGFunction(
        schema="public",
        signature="auth_fn_simulation_entity_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.entity_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_simulation_entity_id)

    public_auth_fn_scientific_artifact_subject_id = PGFunction(
        schema="public",
        signature="auth_fn_scientific_artifact_subject_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                IF NEW.subject_id IS NULL THEN RETURN NEW; END IF;\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.subject_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_scientific_artifact_subject_id)

    public_auth_fn_memodel_calibration_result_calibrated_entity_id = PGFunction(
        schema="public",
        signature="auth_fn_memodel_calibration_result_calibrated_entity_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.calibrated_entity_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_memodel_calibration_result_calibrated_entity_id)

    public_auth_fn_memodel_morphology_id = PGFunction(
        schema="public",
        signature="auth_fn_memodel_morphology_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.morphology_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_memodel_morphology_id)

    public_auth_fn_memodel_emodel_id = PGFunction(
        schema="public",
        signature="auth_fn_memodel_emodel_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.emodel_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_memodel_emodel_id)

    public_auth_fn_experimental_synapses_per_connection_subject_id = PGFunction(
        schema="public",
        signature="auth_fn_experimental_synapses_per_connection_subject_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                IF NEW.subject_id IS NULL THEN RETURN NEW; END IF;\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.subject_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_experimental_synapses_per_connection_subject_id)

    public_auth_fn_experimental_neuron_density_subject_id = PGFunction(
        schema="public",
        signature="auth_fn_experimental_neuron_density_subject_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                IF NEW.subject_id IS NULL THEN RETURN NEW; END IF;\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.subject_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_experimental_neuron_density_subject_id)

    public_auth_fn_experimental_bouton_density_subject_id = PGFunction(
        schema="public",
        signature="auth_fn_experimental_bouton_density_subject_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                IF NEW.subject_id IS NULL THEN RETURN NEW; END IF;\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.subject_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_experimental_bouton_density_subject_id)

    public_auth_fn_emodel_exemplar_morphology_id = PGFunction(
        schema="public",
        signature="auth_fn_emodel_exemplar_morphology_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.exemplar_morphology_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_emodel_exemplar_morphology_id)

    public_auth_fn_em_cell_mesh_em_dense_reconstruction_dataset_id = PGFunction(
        schema="public",
        signature="auth_fn_em_cell_mesh_em_dense_reconstruction_dataset_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.em_dense_reconstruction_dataset_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_em_cell_mesh_em_dense_reconstruction_dataset_id)

    public_auth_fn_electrical_recording_stimulus_recording_id = PGFunction(
        schema="public",
        signature="auth_fn_electrical_recording_stimulus_recording_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.recording_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_electrical_recording_stimulus_recording_id)

    public_auth_fn_circuit_root_circuit_id = PGFunction(
        schema="public",
        signature="auth_fn_circuit_root_circuit_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                IF NEW.root_circuit_id IS NULL THEN RETURN NEW; END IF;\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.root_circuit_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_circuit_root_circuit_id)

    public_auth_fn_circuit_atlas_id = PGFunction(
        schema="public",
        signature="auth_fn_circuit_atlas_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                IF NEW.atlas_id IS NULL THEN RETURN NEW; END IF;\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.atlas_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_circuit_atlas_id)

    public_auth_fn_cell_morphology_cell_morphology_protocol_id = PGFunction(
        schema="public",
        signature="auth_fn_cell_morphology_cell_morphology_protocol_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                IF NEW.cell_morphology_protocol_id IS NULL THEN RETURN NEW; END IF;\n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.cell_morphology_protocol_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_cell_morphology_cell_morphology_protocol_id)

    public_auth_fn_brain_atlas_region_brain_atlas_id = PGFunction(
        schema="public",
        signature="auth_fn_brain_atlas_region_brain_atlas_id()",
        definition="RETURNS TRIGGER AS $$\n            BEGIN\n                \n                IF NOT EXISTS (\n                    SELECT 1 FROM entity e1\n                    JOIN entity e2 ON e2.id = NEW.id\n                    WHERE e1.id = NEW.brain_atlas_id\n                    AND (e1.authorized_public = TRUE\n                        OR (e2.authorized_public = FALSE\n                            AND e1.authorized_project_id = e2.authorized_project_id\n                        )\n                    )\n                ) THEN\n                    RAISE EXCEPTION 'unauthorized private reference'\n                        USING ERRCODE = '42501'; -- Insufficient Privilege\n                END IF;\n                RETURN NEW;\n            END;\n            $$ LANGUAGE plpgsql",
    )
    op.drop_entity(public_auth_fn_brain_atlas_region_brain_atlas_id)

    # ### end Alembic commands ###
