#!/bin/bash
# Automatically generated, do not edit!
set -euo pipefail
echo "DB DUMP (version 1 for db version 805fc8028f39)"


MAKESELF_BIN="${MAKESELF_BIN:-makeself}"
if ! command -v "$MAKESELF_BIN" &>/dev/null; then
    echo "Error: makeself not found, please set the correct MAKESELF_BIN variable."
    exit 1
fi
MAKESELF_PARAMS="${MAKESELF_PARAMS:-}"
MAKESELF="${MAKESELF_BIN} ${MAKESELF_PARAMS}"


export PGUSER="${PGUSER:-entitycore}"
export PGHOST="${PGHOST:-127.0.0.1}"
export PGPORT="${PGPORT:-5432}"
export PGDATABASE="${PGDATABASE:-entitycore}"

PSQL_BIN="${PSQL_BIN:-psql}"
PSQL_PARAMS="${PSQL_PARAMS:--q --echo-errors --set=ON_ERROR_STOP=on}"
PSQL="${PSQL_BIN} ${PSQL_PARAMS}"

PG_DUMP_BIN="${PG_DUMP_BIN:-pg_dump}"
PG_DUMP_PARAMS="${PG_DUMP_PARAMS:-}"
PG_DUMP="${PG_DUMP_BIN} ${PG_DUMP_PARAMS}"

if ! command -v "$PSQL_BIN" &>/dev/null; then
    echo "Error: psql not found, please set the correct PSQL_BIN variable."
    exit 1
fi

if ! command -v "$PG_DUMP_BIN" &>/dev/null; then
    echo "Error: pg_dump not found, please set the correct PG_DUMP_BIN variable."
    exit 1
fi

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

SCRIPT_DB_VERSION="805fc8028f39"
DB_VERSION=$($PSQL -t -A -c "SELECT version_num FROM alembic_version")
if [[ "$DB_VERSION" != "$SCRIPT_DB_VERSION" ]]; then
    echo "Actual database version ($DB_VERSION) != script version ($SCRIPT_DB_VERSION)"
    exit 1
fi

SCRIPT_DIR="$(realpath "$(dirname "$0")")"
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
\echo Dumping table alembic_version
\copy (SELECT alembic_version.* FROM alembic_version) TO '$DATA_DIR/alembic_version.csv' WITH CSV HEADER;
\echo Dumping table agent
\copy (SELECT agent.* FROM agent) TO '$DATA_DIR/agent.csv' WITH CSV HEADER;
\echo Dumping table brain_region
\copy (SELECT brain_region.* FROM brain_region) TO '$DATA_DIR/brain_region.csv' WITH CSV HEADER;
\echo Dumping table brain_region_hierarchy
\copy (SELECT brain_region_hierarchy.* FROM brain_region_hierarchy) TO '$DATA_DIR/brain_region_hierarchy.csv' WITH CSV HEADER;
\echo Dumping table annotation_body
\copy (SELECT annotation_body.* FROM annotation_body) TO '$DATA_DIR/annotation_body.csv' WITH CSV HEADER;
\echo Dumping table consortium
\copy (SELECT consortium.* FROM consortium) TO '$DATA_DIR/consortium.csv' WITH CSV HEADER;
\echo Dumping table datamaturity_annotation_body
\copy (SELECT datamaturity_annotation_body.* FROM datamaturity_annotation_body) TO '$DATA_DIR/datamaturity_annotation_body.csv' WITH CSV HEADER;
\echo Dumping table etype_class
\copy (SELECT etype_class.* FROM etype_class) TO '$DATA_DIR/etype_class.csv' WITH CSV HEADER;
\echo Dumping table external_url
\copy (SELECT external_url.* FROM external_url) TO '$DATA_DIR/external_url.csv' WITH CSV HEADER;
\echo Dumping table ion
\copy (SELECT ion.* FROM ion) TO '$DATA_DIR/ion.csv' WITH CSV HEADER;
\echo Dumping table ion_channel
\copy (SELECT ion_channel.* FROM ion_channel) TO '$DATA_DIR/ion_channel.csv' WITH CSV HEADER;
\echo Dumping table license
\copy (SELECT license.* FROM license) TO '$DATA_DIR/license.csv' WITH CSV HEADER;
\echo Dumping table mtype_class
\copy (SELECT mtype_class.* FROM mtype_class) TO '$DATA_DIR/mtype_class.csv' WITH CSV HEADER;
\echo Dumping table organization
\copy (SELECT organization.* FROM organization) TO '$DATA_DIR/organization.csv' WITH CSV HEADER;
\echo Dumping table person
\copy (SELECT person.* FROM person) TO '$DATA_DIR/person.csv' WITH CSV HEADER;
\echo Dumping table publication
\copy (SELECT publication.* FROM publication) TO '$DATA_DIR/publication.csv' WITH CSV HEADER;
\echo Dumping table role
\copy (SELECT role.* FROM role) TO '$DATA_DIR/role.csv' WITH CSV HEADER;
\echo Dumping table species
\copy (SELECT species.* FROM species) TO '$DATA_DIR/species.csv' WITH CSV HEADER;
\echo Dumping table strain
\copy (SELECT strain.* FROM strain) TO '$DATA_DIR/strain.csv' WITH CSV HEADER;
\echo Dumping table entity
\copy (SELECT entity.* from entity WHERE authorized_public IS true) TO '$DATA_DIR/entity.csv' WITH CSV HEADER;
\echo Dumping table activity
\copy (SELECT activity.* from activity WHERE authorized_public IS true) TO '$DATA_DIR/activity.csv' WITH CSV HEADER;
\echo Dumping table analysis_notebook_environment
\copy (SELECT analysis_notebook_environment.* from analysis_notebook_environment JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/analysis_notebook_environment.csv' WITH CSV HEADER;
\echo Dumping table analysis_notebook_result
\copy (SELECT analysis_notebook_result.* from analysis_notebook_result JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/analysis_notebook_result.csv' WITH CSV HEADER;
\echo Dumping table analysis_notebook_template
\copy (SELECT analysis_notebook_template.* from analysis_notebook_template JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/analysis_notebook_template.csv' WITH CSV HEADER;
\echo Dumping table analysis_software_source_code
\copy (SELECT analysis_software_source_code.* from analysis_software_source_code JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/analysis_software_source_code.csv' WITH CSV HEADER;
\echo Dumping table brain_atlas
\copy (SELECT brain_atlas.* from brain_atlas JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/brain_atlas.csv' WITH CSV HEADER;
\echo Dumping table brain_atlas_region
\copy (SELECT brain_atlas_region.* from brain_atlas_region JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/brain_atlas_region.csv' WITH CSV HEADER;
\echo Dumping table cell_composition
\copy (SELECT cell_composition.* from cell_composition JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/cell_composition.csv' WITH CSV HEADER;
\echo Dumping table cell_morphology
\copy (SELECT cell_morphology.* from cell_morphology JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/cell_morphology.csv' WITH CSV HEADER;
\echo Dumping table cell_morphology_protocol
\copy (SELECT cell_morphology_protocol.* from cell_morphology_protocol JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/cell_morphology_protocol.csv' WITH CSV HEADER;
\echo Dumping table circuit
\copy (SELECT circuit.* from circuit JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/circuit.csv' WITH CSV HEADER;
\echo Dumping table electrical_cell_recording
\copy (SELECT electrical_cell_recording.* from electrical_cell_recording JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/electrical_cell_recording.csv' WITH CSV HEADER;
\echo Dumping table electrical_recording
\copy (SELECT electrical_recording.* from electrical_recording JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/electrical_recording.csv' WITH CSV HEADER;
\echo Dumping table electrical_recording_stimulus
\copy (SELECT electrical_recording_stimulus.* from electrical_recording_stimulus JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/electrical_recording_stimulus.csv' WITH CSV HEADER;
\echo Dumping table em_cell_mesh
\copy (SELECT em_cell_mesh.* from em_cell_mesh JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/em_cell_mesh.csv' WITH CSV HEADER;
\echo Dumping table em_dense_reconstruction_dataset
\copy (SELECT em_dense_reconstruction_dataset.* from em_dense_reconstruction_dataset JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/em_dense_reconstruction_dataset.csv' WITH CSV HEADER;
\echo Dumping table emodel
\copy (SELECT emodel.* from emodel JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/emodel.csv' WITH CSV HEADER;
\echo Dumping table scientific_artifact
\copy (SELECT scientific_artifact.* from scientific_artifact JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/scientific_artifact.csv' WITH CSV HEADER;
\echo Dumping table experimental_bouton_density
\copy (SELECT experimental_bouton_density.* from experimental_bouton_density JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/experimental_bouton_density.csv' WITH CSV HEADER;
\echo Dumping table experimental_neuron_density
\copy (SELECT experimental_neuron_density.* from experimental_neuron_density JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/experimental_neuron_density.csv' WITH CSV HEADER;
\echo Dumping table experimental_synapses_per_connection
\copy (SELECT experimental_synapses_per_connection.* from experimental_synapses_per_connection JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/experimental_synapses_per_connection.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_model
\copy (SELECT ion_channel_model.* from ion_channel_model JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/ion_channel_model.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_modeling_campaign
\copy (SELECT ion_channel_modeling_campaign.* from ion_channel_modeling_campaign JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/ion_channel_modeling_campaign.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_modeling_config
\copy (SELECT ion_channel_modeling_config.* from ion_channel_modeling_config JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/ion_channel_modeling_config.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_recording
\copy (SELECT ion_channel_recording.* from ion_channel_recording JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/ion_channel_recording.csv' WITH CSV HEADER;
\echo Dumping table me_type_density
\copy (SELECT me_type_density.* from me_type_density JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/me_type_density.csv' WITH CSV HEADER;
\echo Dumping table memodel
\copy (SELECT memodel.* from memodel JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/memodel.csv' WITH CSV HEADER;
\echo Dumping table simulation
\copy (SELECT simulation.* from simulation JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/simulation.csv' WITH CSV HEADER;
\echo Dumping table simulation_campaign
\copy (SELECT simulation_campaign.* from simulation_campaign JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/simulation_campaign.csv' WITH CSV HEADER;
\echo Dumping table simulation_result
\copy (SELECT simulation_result.* from simulation_result JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/simulation_result.csv' WITH CSV HEADER;
\echo Dumping table single_neuron_simulation
\copy (SELECT single_neuron_simulation.* from single_neuron_simulation JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/single_neuron_simulation.csv' WITH CSV HEADER;
\echo Dumping table single_neuron_synaptome
\copy (SELECT single_neuron_synaptome.* from single_neuron_synaptome JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/single_neuron_synaptome.csv' WITH CSV HEADER;
\echo Dumping table single_neuron_synaptome_simulation
\copy (SELECT single_neuron_synaptome_simulation.* from single_neuron_synaptome_simulation JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/single_neuron_synaptome_simulation.csv' WITH CSV HEADER;
\echo Dumping table subject
\copy (SELECT subject.* from subject JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$DATA_DIR/subject.csv' WITH CSV HEADER;
\echo Dumping table analysis_notebook_execution
\copy (SELECT analysis_notebook_execution.* from analysis_notebook_execution JOIN activity USING (id) WHERE activity.authorized_public IS true) TO '$DATA_DIR/analysis_notebook_execution.csv' WITH CSV HEADER;
\echo Dumping table calibration
\copy (SELECT calibration.* from calibration JOIN activity USING (id) WHERE activity.authorized_public IS true) TO '$DATA_DIR/calibration.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_modeling_config_generation
\copy (SELECT ion_channel_modeling_config_generation.* from ion_channel_modeling_config_generation JOIN activity USING (id) WHERE activity.authorized_public IS true) TO '$DATA_DIR/ion_channel_modeling_config_generation.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_modeling_execution
\copy (SELECT ion_channel_modeling_execution.* from ion_channel_modeling_execution JOIN activity USING (id) WHERE activity.authorized_public IS true) TO '$DATA_DIR/ion_channel_modeling_execution.csv' WITH CSV HEADER;
\echo Dumping table simulation_execution
\copy (SELECT simulation_execution.* from simulation_execution JOIN activity USING (id) WHERE activity.authorized_public IS true) TO '$DATA_DIR/simulation_execution.csv' WITH CSV HEADER;
\echo Dumping table simulation_generation
\copy (SELECT simulation_generation.* from simulation_generation JOIN activity USING (id) WHERE activity.authorized_public IS true) TO '$DATA_DIR/simulation_generation.csv' WITH CSV HEADER;
\echo Dumping table validation
\copy (SELECT validation.* from validation JOIN activity USING (id) WHERE activity.authorized_public IS true) TO '$DATA_DIR/validation.csv' WITH CSV HEADER;
\echo Dumping table annotation
\copy (SELECT annotation.* FROM annotation JOIN entity AS t ON t.id=annotation.entity_id WHERE t.authorized_public IS true) TO '$DATA_DIR/annotation.csv' WITH CSV HEADER;
\echo Dumping table asset
\copy (SELECT asset.* FROM asset JOIN entity AS t ON t.id=asset.entity_id WHERE t.authorized_public IS true) TO '$DATA_DIR/asset.csv' WITH CSV HEADER;
\echo Dumping table contribution
\copy (SELECT contribution.* FROM contribution JOIN entity AS t ON t.id=contribution.entity_id WHERE t.authorized_public IS true) TO '$DATA_DIR/contribution.csv' WITH CSV HEADER;
\echo Dumping table derivation
\copy (SELECT derivation.* FROM derivation JOIN entity AS t1 ON t1.id=derivation.used_id JOIN entity AS t2 ON t2.id=derivation.generated_id WHERE t1.authorized_public IS true AND t2.authorized_public IS true) TO '$DATA_DIR/derivation.csv' WITH CSV HEADER;
\echo Dumping table etype_classification
\copy (SELECT etype_classification.* FROM etype_classification JOIN entity AS e ON e.id=etype_classification.entity_id WHERE etype_classification.authorized_public IS true AND e.authorized_public IS true) TO '$DATA_DIR/etype_classification.csv' WITH CSV HEADER;
\echo Dumping table generation
\copy (SELECT generation.* FROM generation JOIN entity AS t1 ON t1.id=generation.generation_entity_id JOIN activity AS t2 ON t2.id=generation.generation_activity_id WHERE t1.authorized_public IS true AND t2.authorized_public IS true) TO '$DATA_DIR/generation.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_model__emodel
\copy (SELECT ion_channel_model__emodel.* FROM ion_channel_model__emodel JOIN entity AS t1 ON t1.id=ion_channel_model__emodel.ion_channel_model_id JOIN entity AS t2 ON t2.id=ion_channel_model__emodel.emodel_id WHERE t1.authorized_public IS true AND t2.authorized_public IS true) TO '$DATA_DIR/ion_channel_model__emodel.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_recording__ion_channel_modeling_campaign
\copy (SELECT ion_channel_recording__ion_channel_modeling_campaign.* FROM ion_channel_recording__ion_channel_modeling_campaign JOIN entity AS t1 ON t1.id=ion_channel_recording__ion_channel_modeling_campaign.ion_channel_recording_id JOIN entity AS t2 ON t2.id=ion_channel_recording__ion_channel_modeling_campaign.ion_channel_modeling_campaign_id WHERE t1.authorized_public IS true AND t2.authorized_public IS true) TO '$DATA_DIR/ion_channel_recording__ion_channel_modeling_campaign.csv' WITH CSV HEADER;
\echo Dumping table measurement_annotation
\copy (SELECT measurement_annotation.* FROM measurement_annotation JOIN entity AS t ON t.id=measurement_annotation.entity_id WHERE t.authorized_public IS true) TO '$DATA_DIR/measurement_annotation.csv' WITH CSV HEADER;
\echo Dumping table measurement_item
\copy (SELECT measurement_item.* FROM measurement_item JOIN measurement_kind AS mk ON mk.id=measurement_item.measurement_kind_id JOIN measurement_annotation AS ma ON ma.id=mk.measurement_annotation_id JOIN entity AS e ON e.id=ma.entity_id WHERE e.authorized_public IS true) TO '$DATA_DIR/measurement_item.csv' WITH CSV HEADER;
\echo Dumping table measurement_kind
\copy (SELECT measurement_kind.* FROM measurement_kind JOIN measurement_annotation AS ma ON ma.id=measurement_kind.measurement_annotation_id JOIN entity AS e ON e.id=ma.entity_id WHERE e.authorized_public IS true) TO '$DATA_DIR/measurement_kind.csv' WITH CSV HEADER;
\echo Dumping table measurement_record
\copy (SELECT measurement_record.* FROM measurement_record JOIN entity AS t ON t.id=measurement_record.entity_id WHERE t.authorized_public IS true) TO '$DATA_DIR/measurement_record.csv' WITH CSV HEADER;
\echo Dumping table memodel_calibration_result
\copy (SELECT memodel_calibration_result.* FROM memodel_calibration_result JOIN entity AS e1 ON e1.id=memodel_calibration_result.id JOIN entity AS e2 ON e2.id=memodel_calibration_result.calibrated_entity_id WHERE e1.authorized_public IS true AND e2.authorized_public IS true) TO '$DATA_DIR/memodel_calibration_result.csv' WITH CSV HEADER;
\echo Dumping table mtype_classification
\copy (SELECT mtype_classification.* FROM mtype_classification JOIN entity AS e ON e.id=mtype_classification.entity_id WHERE mtype_classification.authorized_public IS true AND e.authorized_public IS true) TO '$DATA_DIR/mtype_classification.csv' WITH CSV HEADER;
\echo Dumping table scientific_artifact_external_url_link
\copy (SELECT scientific_artifact_external_url_link.* FROM scientific_artifact_external_url_link JOIN entity AS t ON t.id=scientific_artifact_external_url_link.scientific_artifact_id WHERE t.authorized_public IS true) TO '$DATA_DIR/scientific_artifact_external_url_link.csv' WITH CSV HEADER;
\echo Dumping table scientific_artifact_publication_link
\copy (SELECT scientific_artifact_publication_link.* FROM scientific_artifact_publication_link JOIN entity AS t ON t.id=scientific_artifact_publication_link.scientific_artifact_id WHERE t.authorized_public IS true) TO '$DATA_DIR/scientific_artifact_publication_link.csv' WITH CSV HEADER;
\echo Dumping table usage
\copy (SELECT usage.* FROM usage JOIN entity AS t1 ON t1.id=usage.usage_entity_id JOIN activity AS t2 ON t2.id=usage.usage_activity_id WHERE t1.authorized_public IS true AND t2.authorized_public IS true) TO '$DATA_DIR/usage.csv' WITH CSV HEADER;
\echo Dumping table validation_result
\copy (SELECT validation_result.* FROM validation_result JOIN entity AS e1 ON e1.id=validation_result.id JOIN entity AS e2 ON e2.id=validation_result.validated_entity_id WHERE e1.authorized_public IS true AND e2.authorized_public IS true) TO '$DATA_DIR/validation_result.csv' WITH CSV HEADER;
COMMIT;
EOF

echo -e "\nBuilding install script..."

install -m 755 /dev/stdin "$WORK_DIR/load.sh" <<'EOF_LOAD_SCRIPT'
#!/bin/bash
# Automatically generated, do not edit!
set -euo pipefail
echo "DB LOAD (version 1 for db version 805fc8028f39)"


export PGUSER="${PGUSER:-entitycore}"
export PGHOST="${PGHOST:-127.0.0.1}"
export PGPORT="${PGPORT:-5432}"
export PGDATABASE="${PGDATABASE:-entitycore}"

PSQL_BIN="${PSQL_BIN:-psql}"
PSQL_PARAMS="${PSQL_PARAMS:--q --echo-errors --set=ON_ERROR_STOP=on}"
PSQL="${PSQL_BIN} ${PSQL_PARAMS}"

PG_DUMP_BIN="${PG_DUMP_BIN:-pg_dump}"
PG_DUMP_PARAMS="${PG_DUMP_PARAMS:-}"
PG_DUMP="${PG_DUMP_BIN} ${PG_DUMP_PARAMS}"

if ! command -v "$PSQL_BIN" &>/dev/null; then
    echo "Error: psql not found, please set the correct PSQL_BIN variable."
    exit 1
fi

if ! command -v "$PG_DUMP_BIN" &>/dev/null; then
    echo "Error: pg_dump not found, please set the correct PG_DUMP_BIN variable."
    exit 1
fi

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

cp "$SCRIPT_DIR/build_database_archive.sh" "$WORK_DIR" # for inspection
LABEL="DB installer (version 1 for db version 805fc8028f39)"
$MAKESELF "$WORK_DIR" "$INSTALL_SCRIPT" "$LABEL" "./load.sh"

echo "All done."
