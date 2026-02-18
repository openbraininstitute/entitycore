#!/bin/bash
# Automatically generated, do not edit!
set -euo pipefail
SCRIPT_VERSION="1"
SCRIPT_DB_VERSION="122df969f6ee"
echo "DB dump (version $SCRIPT_VERSION for db version $SCRIPT_DB_VERSION)"


MAKESELF_BIN="${MAKESELF_BIN:-makeself}"
if ! command -v "$MAKESELF_BIN" &>/dev/null; then
    echo "Error: makeself not found, please set the correct MAKESELF_BIN variable."
    exit 1
fi
MAKESELF_PARAMS="${MAKESELF_PARAMS:-}"
MAKESELF="${MAKESELF_BIN} ${MAKESELF_PARAMS}"


PSQL_BIN="${PSQL_BIN:-psql}"
PSQL_PARAMS="${PSQL_PARAMS:--q --echo-errors --set=ON_ERROR_STOP=on}"
PSQL="${PSQL_BIN} ${PSQL_PARAMS}"
if ! command -v "$PSQL_BIN" &>/dev/null; then
    echo "Error: psql not found, please set the correct PSQL_BIN variable."
    exit 1
fi


PG_DUMP_BIN="${PG_DUMP_BIN:-pg_dump}"
PG_DUMP_PARAMS="${PG_DUMP_PARAMS:---no-owner --no-privileges}"
PG_DUMP="${PG_DUMP_BIN} ${PG_DUMP_PARAMS}"
if ! command -v "$PG_DUMP_BIN" &>/dev/null; then
    echo "Error: pg_dump not found, please set the correct PG_DUMP_BIN variable."
    exit 1
fi


export PGUSER="${PGUSER:-entitycore}"
export PGHOST="${PGHOST:-127.0.0.1}"
export PGPORT="${PGPORT:-5432}"
export PGDATABASE="${PGDATABASE:-entitycore}"
if [[ -z "${PGPASSWORD:-}" ]]; then
    read -r -s -p "Enter password for postgresql://$PGUSER@$PGHOST:$PGPORT/$PGDATABASE: " PGPASSWORD
    echo
    export PGPASSWORD
fi


WORK_DIR=$(mktemp -d)
cleanup() {
    printf '\nCleaning up %s\n' "$WORK_DIR"
    rm -rf "$WORK_DIR"
}
trap cleanup EXIT

DATA_DIR="$WORK_DIR/data"
SCHEMA_PRE_DATA="$DATA_DIR/schema_pre_data.sql"
SCHEMA_POST_DATA="$DATA_DIR/schema_post_data.sql"

ACTUAL_DB_VERSION=$($PSQL -t -A -c "SELECT version_num FROM alembic_version")
if [[ "$ACTUAL_DB_VERSION" != "$SCRIPT_DB_VERSION" ]]; then
    echo "Actual db version ($ACTUAL_DB_VERSION) != script version ($SCRIPT_DB_VERSION)"
    exit 1
fi

INSTALL_SCRIPT="install_db_$(date +%Y%m%d)_$SCRIPT_DB_VERSION.run"

echo "Dump database $PGDATABASE from $PGHOST:$PGPORT"

mkdir -p "$DATA_DIR"

echo "Dumping schema..."
$PG_DUMP --schema-only --format=p --section=pre-data > "$SCHEMA_PRE_DATA"
$PG_DUMP --schema-only --format=p --section=post-data > "$SCHEMA_POST_DATA"

echo "Dumping data..."
$PSQL <<EOF
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SET TRANSACTION READ ONLY;
\echo Dumping table activity
\copy (SELECT t0.* FROM activity AS t0  WHERE t0.authorized_public IS true) TO '$DATA_DIR/activity.csv' WITH CSV HEADER;
\echo Dumping table agent
\copy (SELECT t0.* FROM agent AS t0  WHERE TRUE) TO '$DATA_DIR/agent.csv' WITH CSV HEADER;
\echo Dumping table analysis_notebook_environment
\copy (SELECT t0.* FROM analysis_notebook_environment AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/analysis_notebook_environment.csv' WITH CSV HEADER;
\echo Dumping table analysis_notebook_execution
\copy (SELECT t0.* FROM analysis_notebook_execution AS t0 JOIN activity AS t1 ON t1.id=t0.id LEFT JOIN entity AS t2 ON t2.id=t0.analysis_notebook_template_id JOIN entity AS t3 ON t3.id=t0.analysis_notebook_environment_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false AND t3.authorized_public IS NOT false) TO '$DATA_DIR/analysis_notebook_execution.csv' WITH CSV HEADER;
\echo Dumping table analysis_notebook_result
\copy (SELECT t0.* FROM analysis_notebook_result AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/analysis_notebook_result.csv' WITH CSV HEADER;
\echo Dumping table analysis_notebook_template
\copy (SELECT t0.* FROM analysis_notebook_template AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/analysis_notebook_template.csv' WITH CSV HEADER;
\echo Dumping table analysis_software_source_code
\copy (SELECT t0.* FROM analysis_software_source_code AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/analysis_software_source_code.csv' WITH CSV HEADER;
\echo Dumping table annotation
\copy (SELECT t0.* FROM annotation AS t0 JOIN entity AS t1 ON t1.id=t0.entity_id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/annotation.csv' WITH CSV HEADER;
\echo Dumping table annotation_body
\copy (SELECT t0.* FROM annotation_body AS t0  WHERE TRUE) TO '$DATA_DIR/annotation_body.csv' WITH CSV HEADER;
\echo Dumping table asset
\copy (SELECT t0.* FROM asset AS t0 JOIN entity AS t1 ON t1.id=t0.entity_id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/asset.csv' WITH CSV HEADER;
\echo Dumping table brain_atlas
\copy (SELECT t0.* FROM brain_atlas AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/brain_atlas.csv' WITH CSV HEADER;
\echo Dumping table brain_atlas_region
\copy (SELECT t0.* FROM brain_atlas_region AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.brain_atlas_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/brain_atlas_region.csv' WITH CSV HEADER;
\echo Dumping table brain_region
\copy (SELECT t0.* FROM brain_region AS t0  WHERE TRUE) TO '$DATA_DIR/brain_region.csv' WITH CSV HEADER;
\echo Dumping table brain_region_hierarchy
\copy (SELECT t0.* FROM brain_region_hierarchy AS t0  WHERE TRUE) TO '$DATA_DIR/brain_region_hierarchy.csv' WITH CSV HEADER;
\echo Dumping table calibration
\copy (SELECT t0.* FROM calibration AS t0 JOIN activity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/calibration.csv' WITH CSV HEADER;
\echo Dumping table campaign
\copy (SELECT t0.* FROM campaign AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/campaign.csv' WITH CSV HEADER;
\echo Dumping table cell_composition
\copy (SELECT t0.* FROM cell_composition AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/cell_composition.csv' WITH CSV HEADER;
\echo Dumping table cell_morphology
\copy (SELECT t0.* FROM cell_morphology AS t0 JOIN entity AS t1 ON t1.id=t0.id LEFT JOIN entity AS t2 ON t2.id=t0.cell_morphology_protocol_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/cell_morphology.csv' WITH CSV HEADER;
\echo Dumping table cell_morphology_protocol
\copy (SELECT t0.* FROM cell_morphology_protocol AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/cell_morphology_protocol.csv' WITH CSV HEADER;
\echo Dumping table circuit
\copy (SELECT t0.* FROM circuit AS t0 JOIN entity AS t1 ON t1.id=t0.id LEFT JOIN entity AS t2 ON t2.id=t0.root_circuit_id LEFT JOIN entity AS t3 ON t3.id=t0.atlas_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false AND t3.authorized_public IS NOT false) TO '$DATA_DIR/circuit.csv' WITH CSV HEADER;
\echo Dumping table circuit_extraction_campaign
\copy (SELECT t0.* FROM circuit_extraction_campaign AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/circuit_extraction_campaign.csv' WITH CSV HEADER;
\echo Dumping table circuit_extraction_config
\copy (SELECT t0.* FROM circuit_extraction_config AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.circuit_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/circuit_extraction_config.csv' WITH CSV HEADER;
\echo Dumping table circuit_extraction_config_generation
\copy (SELECT t0.* FROM circuit_extraction_config_generation AS t0 JOIN activity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/circuit_extraction_config_generation.csv' WITH CSV HEADER;
\echo Dumping table circuit_extraction_execution
\copy (SELECT t0.* FROM circuit_extraction_execution AS t0 JOIN activity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/circuit_extraction_execution.csv' WITH CSV HEADER;
\echo Dumping table task_execution
\copy (SELECT t0.* FROM task_execution AS t0 JOIN activity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/task_execution.csv' WITH CSV HEADER;
\echo Dumping table config_generation
\copy (SELECT t0.* FROM config_generation AS t0 JOIN activity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/config_generation.csv' WITH CSV HEADER;
\echo Dumping table consortium
\copy (SELECT t0.* FROM consortium AS t0  WHERE TRUE) TO '$DATA_DIR/consortium.csv' WITH CSV HEADER;
\echo Dumping table contribution
\copy (SELECT t0.* FROM contribution AS t0 JOIN entity AS t1 ON t1.id=t0.entity_id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/contribution.csv' WITH CSV HEADER;
\echo Dumping table datamaturity_annotation_body
\copy (SELECT t0.* FROM datamaturity_annotation_body AS t0  WHERE TRUE) TO '$DATA_DIR/datamaturity_annotation_body.csv' WITH CSV HEADER;
\echo Dumping table derivation
\copy (SELECT t0.* FROM derivation AS t0 JOIN entity AS t1 ON t1.id=t0.used_id JOIN entity AS t2 ON t2.id=t0.generated_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/derivation.csv' WITH CSV HEADER;
\echo Dumping table electrical_cell_recording
\copy (SELECT t0.* FROM electrical_cell_recording AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/electrical_cell_recording.csv' WITH CSV HEADER;
\echo Dumping table electrical_recording
\copy (SELECT t0.* FROM electrical_recording AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/electrical_recording.csv' WITH CSV HEADER;
\echo Dumping table electrical_recording_stimulus
\copy (SELECT t0.* FROM electrical_recording_stimulus AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.recording_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/electrical_recording_stimulus.csv' WITH CSV HEADER;
\echo Dumping table em_cell_mesh
\copy (SELECT t0.* FROM em_cell_mesh AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.em_dense_reconstruction_dataset_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/em_cell_mesh.csv' WITH CSV HEADER;
\echo Dumping table em_cell_mesh__skeletonization_campaign
\copy (SELECT t0.* FROM em_cell_mesh__skeletonization_campaign AS t0 JOIN entity AS t1 ON t1.id=t0.em_cell_mesh_id JOIN entity AS t2 ON t2.id=t0.skeletonization_campaign_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/em_cell_mesh__skeletonization_campaign.csv' WITH CSV HEADER;
\echo Dumping table em_dense_reconstruction_dataset
\copy (SELECT t0.* FROM em_dense_reconstruction_dataset AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/em_dense_reconstruction_dataset.csv' WITH CSV HEADER;
\echo Dumping table emodel
\copy (SELECT t0.* FROM emodel AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.exemplar_morphology_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/emodel.csv' WITH CSV HEADER;
\echo Dumping table entity
\copy (SELECT t0.* FROM entity AS t0  WHERE t0.authorized_public IS true) TO '$DATA_DIR/entity.csv' WITH CSV HEADER;
\echo Dumping table entity__campaign
\copy (SELECT t0.* FROM entity__campaign AS t0 JOIN entity AS t1 ON t1.id=t0.entity_id JOIN entity AS t2 ON t2.id=t0.campaign_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/entity__campaign.csv' WITH CSV HEADER;
\echo Dumping table entity__task_config
\copy (SELECT t0.* FROM entity__task_config AS t0 JOIN entity AS t1 ON t1.id=t0.entity_id JOIN entity AS t2 ON t2.id=t0.task_config_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/entity__task_config.csv' WITH CSV HEADER;
\echo Dumping table etype_class
\copy (SELECT t0.* FROM etype_class AS t0  WHERE TRUE) TO '$DATA_DIR/etype_class.csv' WITH CSV HEADER;
\echo Dumping table etype_classification
\copy (SELECT t0.* FROM etype_classification AS t0 JOIN entity AS t1 ON t1.id=t0.entity_id WHERE t0.authorized_public IS true AND t1.authorized_public IS NOT false) TO '$DATA_DIR/etype_classification.csv' WITH CSV HEADER;
\echo Dumping table experimental_bouton_density
\copy (SELECT t0.* FROM experimental_bouton_density AS t0 JOIN entity AS t1 ON t1.id=t0.id LEFT JOIN entity AS t2 ON t2.id=t0.subject_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/experimental_bouton_density.csv' WITH CSV HEADER;
\echo Dumping table experimental_neuron_density
\copy (SELECT t0.* FROM experimental_neuron_density AS t0 JOIN entity AS t1 ON t1.id=t0.id LEFT JOIN entity AS t2 ON t2.id=t0.subject_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/experimental_neuron_density.csv' WITH CSV HEADER;
\echo Dumping table experimental_synapses_per_connection
\copy (SELECT t0.* FROM experimental_synapses_per_connection AS t0 JOIN entity AS t1 ON t1.id=t0.id LEFT JOIN entity AS t2 ON t2.id=t0.subject_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/experimental_synapses_per_connection.csv' WITH CSV HEADER;
\echo Dumping table external_url
\copy (SELECT t0.* FROM external_url AS t0  WHERE TRUE) TO '$DATA_DIR/external_url.csv' WITH CSV HEADER;
\echo Dumping table generation
\copy (SELECT t0.* FROM generation AS t0 JOIN entity AS t1 ON t1.id=t0.generation_entity_id JOIN activity AS t2 ON t2.id=t0.generation_activity_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/generation.csv' WITH CSV HEADER;
\echo Dumping table ion
\copy (SELECT t0.* FROM ion AS t0  WHERE TRUE) TO '$DATA_DIR/ion.csv' WITH CSV HEADER;
\echo Dumping table ion_channel
\copy (SELECT t0.* FROM ion_channel AS t0  WHERE TRUE) TO '$DATA_DIR/ion_channel.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_model
\copy (SELECT t0.* FROM ion_channel_model AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/ion_channel_model.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_model__emodel
\copy (SELECT t0.* FROM ion_channel_model__emodel AS t0 JOIN entity AS t1 ON t1.id=t0.ion_channel_model_id JOIN entity AS t2 ON t2.id=t0.emodel_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/ion_channel_model__emodel.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_modeling_campaign
\copy (SELECT t0.* FROM ion_channel_modeling_campaign AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/ion_channel_modeling_campaign.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_modeling_config
\copy (SELECT t0.* FROM ion_channel_modeling_config AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.ion_channel_modeling_campaign_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/ion_channel_modeling_config.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_modeling_config_generation
\copy (SELECT t0.* FROM ion_channel_modeling_config_generation AS t0 JOIN activity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/ion_channel_modeling_config_generation.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_modeling_execution
\copy (SELECT t0.* FROM ion_channel_modeling_execution AS t0 JOIN activity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/ion_channel_modeling_execution.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_recording
\copy (SELECT t0.* FROM ion_channel_recording AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/ion_channel_recording.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_recording__ion_channel_modeling_campaign
\copy (SELECT t0.* FROM ion_channel_recording__ion_channel_modeling_campaign AS t0 JOIN entity AS t1 ON t1.id=t0.ion_channel_recording_id JOIN entity AS t2 ON t2.id=t0.ion_channel_modeling_campaign_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/ion_channel_recording__ion_channel_modeling_campaign.csv' WITH CSV HEADER;
\echo Dumping table task_config
\copy (SELECT t0.* FROM task_config AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.campaign_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/task_config.csv' WITH CSV HEADER;
\echo Dumping table license
\copy (SELECT t0.* FROM license AS t0  WHERE TRUE) TO '$DATA_DIR/license.csv' WITH CSV HEADER;
\echo Dumping table me_type_density
\copy (SELECT t0.* FROM me_type_density AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/me_type_density.csv' WITH CSV HEADER;
\echo Dumping table measurement_annotation
\copy (SELECT t0.* FROM measurement_annotation AS t0 JOIN entity AS t1 ON t1.id=t0.entity_id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/measurement_annotation.csv' WITH CSV HEADER;
\echo Dumping table measurement_item
\copy (SELECT t0.* FROM measurement_item AS t0 JOIN measurement_kind AS mk ON mk.id=t0.measurement_kind_id JOIN measurement_annotation AS ma ON ma.id=mk.measurement_annotation_id JOIN entity AS e ON e.id=ma.entity_id WHERE e.authorized_public IS true) TO '$DATA_DIR/measurement_item.csv' WITH CSV HEADER;
\echo Dumping table measurement_kind
\copy (SELECT t0.* FROM measurement_kind AS t0 JOIN measurement_annotation AS ma ON ma.id=t0.measurement_annotation_id JOIN entity AS e ON e.id=ma.entity_id WHERE e.authorized_public IS true) TO '$DATA_DIR/measurement_kind.csv' WITH CSV HEADER;
\echo Dumping table measurement_label
\copy (SELECT t0.* FROM measurement_label AS t0  WHERE TRUE) TO '$DATA_DIR/measurement_label.csv' WITH CSV HEADER;
\echo Dumping table measurement_record
\copy (SELECT t0.* FROM measurement_record AS t0 JOIN entity AS t1 ON t1.id=t0.entity_id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/measurement_record.csv' WITH CSV HEADER;
\echo Dumping table memodel
\copy (SELECT t0.* FROM memodel AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.morphology_id JOIN entity AS t3 ON t3.id=t0.emodel_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false AND t3.authorized_public IS NOT false) TO '$DATA_DIR/memodel.csv' WITH CSV HEADER;
\echo Dumping table memodel_calibration_result
\copy (SELECT t0.* FROM memodel_calibration_result AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.calibrated_entity_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/memodel_calibration_result.csv' WITH CSV HEADER;
\echo Dumping table mtype_class
\copy (SELECT t0.* FROM mtype_class AS t0  WHERE TRUE) TO '$DATA_DIR/mtype_class.csv' WITH CSV HEADER;
\echo Dumping table mtype_classification
\copy (SELECT t0.* FROM mtype_classification AS t0 JOIN entity AS t1 ON t1.id=t0.entity_id WHERE t0.authorized_public IS true AND t1.authorized_public IS NOT false) TO '$DATA_DIR/mtype_classification.csv' WITH CSV HEADER;
\echo Dumping table organization
\copy (SELECT t0.* FROM organization AS t0  WHERE TRUE) TO '$DATA_DIR/organization.csv' WITH CSV HEADER;
\echo Dumping table person
\copy (SELECT t0.* FROM person AS t0  WHERE TRUE) TO '$DATA_DIR/person.csv' WITH CSV HEADER;
\echo Dumping table publication
\copy (SELECT t0.* FROM publication AS t0  WHERE TRUE) TO '$DATA_DIR/publication.csv' WITH CSV HEADER;
\echo Dumping table role
\copy (SELECT t0.* FROM role AS t0  WHERE TRUE) TO '$DATA_DIR/role.csv' WITH CSV HEADER;
\echo Dumping table scientific_artifact
\copy (SELECT t0.* FROM scientific_artifact AS t0 JOIN entity AS t1 ON t1.id=t0.id LEFT JOIN entity AS t2 ON t2.id=t0.subject_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/scientific_artifact.csv' WITH CSV HEADER;
\echo Dumping table scientific_artifact_external_url_link
\copy (SELECT t0.* FROM scientific_artifact_external_url_link AS t0 JOIN entity AS t1 ON t1.id=t0.scientific_artifact_id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/scientific_artifact_external_url_link.csv' WITH CSV HEADER;
\echo Dumping table scientific_artifact_publication_link
\copy (SELECT t0.* FROM scientific_artifact_publication_link AS t0 JOIN entity AS t1 ON t1.id=t0.scientific_artifact_id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/scientific_artifact_publication_link.csv' WITH CSV HEADER;
\echo Dumping table simulation
\copy (SELECT t0.* FROM simulation AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.simulation_campaign_id JOIN entity AS t3 ON t3.id=t0.entity_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false AND t3.authorized_public IS NOT false) TO '$DATA_DIR/simulation.csv' WITH CSV HEADER;
\echo Dumping table simulation_campaign
\copy (SELECT t0.* FROM simulation_campaign AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.entity_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/simulation_campaign.csv' WITH CSV HEADER;
\echo Dumping table simulation_execution
\copy (SELECT t0.* FROM simulation_execution AS t0 JOIN activity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/simulation_execution.csv' WITH CSV HEADER;
\echo Dumping table simulation_generation
\copy (SELECT t0.* FROM simulation_generation AS t0 JOIN activity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/simulation_generation.csv' WITH CSV HEADER;
\echo Dumping table simulation_result
\copy (SELECT t0.* FROM simulation_result AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.simulation_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/simulation_result.csv' WITH CSV HEADER;
\echo Dumping table single_neuron_simulation
\copy (SELECT t0.* FROM single_neuron_simulation AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.me_model_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/single_neuron_simulation.csv' WITH CSV HEADER;
\echo Dumping table single_neuron_synaptome
\copy (SELECT t0.* FROM single_neuron_synaptome AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.me_model_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/single_neuron_synaptome.csv' WITH CSV HEADER;
\echo Dumping table single_neuron_synaptome_simulation
\copy (SELECT t0.* FROM single_neuron_synaptome_simulation AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.synaptome_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/single_neuron_synaptome_simulation.csv' WITH CSV HEADER;
\echo Dumping table skeletonization_campaign
\copy (SELECT t0.* FROM skeletonization_campaign AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/skeletonization_campaign.csv' WITH CSV HEADER;
\echo Dumping table skeletonization_config
\copy (SELECT t0.* FROM skeletonization_config AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.skeletonization_campaign_id JOIN entity AS t3 ON t3.id=t0.em_cell_mesh_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false AND t3.authorized_public IS NOT false) TO '$DATA_DIR/skeletonization_config.csv' WITH CSV HEADER;
\echo Dumping table skeletonization_config_generation
\copy (SELECT t0.* FROM skeletonization_config_generation AS t0 JOIN activity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/skeletonization_config_generation.csv' WITH CSV HEADER;
\echo Dumping table skeletonization_execution
\copy (SELECT t0.* FROM skeletonization_execution AS t0 JOIN activity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/skeletonization_execution.csv' WITH CSV HEADER;
\echo Dumping table species
\copy (SELECT t0.* FROM species AS t0  WHERE TRUE) TO '$DATA_DIR/species.csv' WITH CSV HEADER;
\echo Dumping table strain
\copy (SELECT t0.* FROM strain AS t0  WHERE TRUE) TO '$DATA_DIR/strain.csv' WITH CSV HEADER;
\echo Dumping table subject
\copy (SELECT t0.* FROM subject AS t0 JOIN entity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/subject.csv' WITH CSV HEADER;
\echo Dumping table usage
\copy (SELECT t0.* FROM usage AS t0 JOIN entity AS t1 ON t1.id=t0.usage_entity_id JOIN activity AS t2 ON t2.id=t0.usage_activity_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/usage.csv' WITH CSV HEADER;
\echo Dumping table validation
\copy (SELECT t0.* FROM validation AS t0 JOIN activity AS t1 ON t1.id=t0.id WHERE t1.authorized_public IS NOT false) TO '$DATA_DIR/validation.csv' WITH CSV HEADER;
\echo Dumping table validation_result
\copy (SELECT t0.* FROM validation_result AS t0 JOIN entity AS t1 ON t1.id=t0.id JOIN entity AS t2 ON t2.id=t0.validated_entity_id WHERE t1.authorized_public IS NOT false AND t2.authorized_public IS NOT false) TO '$DATA_DIR/validation_result.csv' WITH CSV HEADER;
\echo Dumping table alembic_version
\copy (SELECT * FROM alembic_version) TO '$DATA_DIR/alembic_version.csv' WITH CSV HEADER;
COMMIT;
EOF

echo -e "\nBuilding install script..."

install -m 755 /dev/stdin "$WORK_DIR/load.sh" <<'EOF_LOAD_SCRIPT'
#!/bin/bash
# Automatically generated, do not edit!
set -euo pipefail
SCRIPT_VERSION="1"
SCRIPT_DB_VERSION="122df969f6ee"
echo "DB load (version $SCRIPT_VERSION for db version $SCRIPT_DB_VERSION)"


PSQL_BIN="${PSQL_BIN:-psql}"
PSQL_PARAMS="${PSQL_PARAMS:--q --echo-errors --set=ON_ERROR_STOP=on}"
PSQL="${PSQL_BIN} ${PSQL_PARAMS}"
if ! command -v "$PSQL_BIN" &>/dev/null; then
    echo "Error: psql not found, please set the correct PSQL_BIN variable."
    exit 1
fi


export PGUSER="${PGUSER:-entitycore}"
export PGHOST="${PGHOST:-127.0.0.1}"
export PGPORT="${PGPORT:-5432}"
export PGDATABASE="${PGDATABASE:-entitycore}"
if [[ -z "${PGPASSWORD:-}" ]]; then
    read -r -s -p "Enter password for postgresql://$PGUSER@$PGHOST:$PGPORT/$PGDATABASE: " PGPASSWORD
    echo
    export PGPASSWORD
fi


DATA_DIR="data"
SCHEMA_PRE_DATA="$DATA_DIR/schema_pre_data.sql"
SCHEMA_POST_DATA="$DATA_DIR/schema_post_data.sql"

if [[
    ! -f "${SCHEMA_PRE_DATA:-}" ||
    ! -f "${SCHEMA_POST_DATA:-}" ||
    ! -d "${DATA_DIR:-}"
]]; then
    echo "Data to load not found."
    exit 1
fi

echo "WARNING! All the data in the database $PGDATABASE at $PGHOST:$PGPORT will be deleted!"
read -r -p "Press Enter to continue or Ctrl+C to cancel..."

echo "Dropping and recreating database..."
dropdb --if-exists --force "$PGDATABASE"
createdb "$PGDATABASE"

echo "Restoring schema_pre_data to destination DB..."
$PSQL -f "$SCHEMA_PRE_DATA"

echo "Importing data..."
$PSQL <<EOF
BEGIN;
$(for FILE in "$DATA_DIR"/*.csv; do
    TABLE=$(basename "$FILE" .csv)
    printf '\\echo Restoring table %s\n' "$TABLE"
    printf '\\copy %s FROM '%s' WITH CSV HEADER;\n' "$TABLE" "$FILE"
done)
COMMIT;
EOF

echo "Restoring schema_post_data to destination DB..."
$PSQL -f "$SCHEMA_POST_DATA"

echo "Running ANALYZE..."
$PSQL -c "ANALYZE;"

echo "All done."

EOF_LOAD_SCRIPT

cp "$0" "$WORK_DIR" # for inspection
LABEL="DB installer (version $SCRIPT_VERSION for db version $SCRIPT_DB_VERSION)"
$MAKESELF "$WORK_DIR" "$INSTALL_SCRIPT" "$LABEL" "./load.sh"

echo "All done."
