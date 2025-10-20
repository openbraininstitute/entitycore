#!/bin/bash
# Automatically generated, do not edit!

set -euo pipefail

export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
export PATH=/usr/pgsql-17/bin:$PATH

export PGUSER="${PGUSER:-entitycore}"
export PGHOST="${PGHOST:-127.0.0.1}"
export PGPORT="${PGPORT:-5433}"
export PGDATABASE="${PGDATABASE:-entitycore}"

PSQL="psql --echo-errors --set=ON_ERROR_STOP=on"

WORKDIR=$(mktemp -d -t dump)
DATE=$(date +%Y%m%d)

DUMP_ARCHIVE="${DUMP_ARCHIVE:-dump_db_$DATE.tar.gz}"
SCHEMA_PRE_DATA="$WORKDIR/schema_pre_data.sql"
SCHEMA_POST_DATA="$WORKDIR/schema_post_data.sql"

cleanup() {
    echo -e "\nCleaning up $WORKDIR"
    rm -rf "$WORKDIR"
}
trap cleanup EXIT

if [[ -z "${PGPASSWORD:-}" ]]; then
    read -s -p "Enter password for postgresql://$PGUSER@$PGHOST:$PGPORT/$PGDATABASE: " PGPASSWORD
    echo
    export PGPASSWORD
fi

echo "DB DUMP - version 1"
echo "Dump database $PGDATABASE from $PGHOST:$PGPORT"
echo "WORKDIR=$WORKDIR"

echo "Dumping schema..."
pg_dump --schema-only --format=p --section=pre-data > "$SCHEMA_PRE_DATA"
pg_dump --schema-only --format=p --section=post-data > "$SCHEMA_POST_DATA"

echo "Dumping data..."
$PSQL <<EOF
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SET TRANSACTION READ ONLY;
\echo Dumping table alembic_version
\copy (SELECT alembic_version.* FROM alembic_version) TO '$WORKDIR/alembic_version.csv' WITH CSV HEADER;
\echo Dumping table agent
\copy (SELECT agent.* FROM agent) TO '$WORKDIR/agent.csv' WITH CSV HEADER;
\echo Dumping table brain_region
\copy (SELECT brain_region.* FROM brain_region) TO '$WORKDIR/brain_region.csv' WITH CSV HEADER;
\echo Dumping table brain_region_hierarchy
\copy (SELECT brain_region_hierarchy.* FROM brain_region_hierarchy) TO '$WORKDIR/brain_region_hierarchy.csv' WITH CSV HEADER;
\echo Dumping table annotation_body
\copy (SELECT annotation_body.* FROM annotation_body) TO '$WORKDIR/annotation_body.csv' WITH CSV HEADER;
\echo Dumping table consortium
\copy (SELECT consortium.* FROM consortium) TO '$WORKDIR/consortium.csv' WITH CSV HEADER;
\echo Dumping table datamaturity_annotation_body
\copy (SELECT datamaturity_annotation_body.* FROM datamaturity_annotation_body) TO '$WORKDIR/datamaturity_annotation_body.csv' WITH CSV HEADER;
\echo Dumping table etype_class
\copy (SELECT etype_class.* FROM etype_class) TO '$WORKDIR/etype_class.csv' WITH CSV HEADER;
\echo Dumping table external_url
\copy (SELECT external_url.* FROM external_url) TO '$WORKDIR/external_url.csv' WITH CSV HEADER;
\echo Dumping table ion
\copy (SELECT ion.* FROM ion) TO '$WORKDIR/ion.csv' WITH CSV HEADER;
\echo Dumping table ion_channel
\copy (SELECT ion_channel.* FROM ion_channel) TO '$WORKDIR/ion_channel.csv' WITH CSV HEADER;
\echo Dumping table license
\copy (SELECT license.* FROM license) TO '$WORKDIR/license.csv' WITH CSV HEADER;
\echo Dumping table mtype_class
\copy (SELECT mtype_class.* FROM mtype_class) TO '$WORKDIR/mtype_class.csv' WITH CSV HEADER;
\echo Dumping table organization
\copy (SELECT organization.* FROM organization) TO '$WORKDIR/organization.csv' WITH CSV HEADER;
\echo Dumping table person
\copy (SELECT person.* FROM person) TO '$WORKDIR/person.csv' WITH CSV HEADER;
\echo Dumping table publication
\copy (SELECT publication.* FROM publication) TO '$WORKDIR/publication.csv' WITH CSV HEADER;
\echo Dumping table role
\copy (SELECT role.* FROM role) TO '$WORKDIR/role.csv' WITH CSV HEADER;
\echo Dumping table species
\copy (SELECT species.* FROM species) TO '$WORKDIR/species.csv' WITH CSV HEADER;
\echo Dumping table strain
\copy (SELECT strain.* FROM strain) TO '$WORKDIR/strain.csv' WITH CSV HEADER;
\echo Dumping table entity
\copy (SELECT entity.* from entity WHERE authorized_public IS true) TO '$WORKDIR/entity.csv' WITH CSV HEADER;
\echo Dumping table activity
\copy (SELECT activity.* from activity WHERE authorized_public IS true) TO '$WORKDIR/activity.csv' WITH CSV HEADER;
\echo Dumping table analysis_notebook_environment
\copy (SELECT analysis_notebook_environment.* from analysis_notebook_environment JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/analysis_notebook_environment.csv' WITH CSV HEADER;
\echo Dumping table analysis_notebook_result
\copy (SELECT analysis_notebook_result.* from analysis_notebook_result JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/analysis_notebook_result.csv' WITH CSV HEADER;
\echo Dumping table analysis_notebook_template
\copy (SELECT analysis_notebook_template.* from analysis_notebook_template JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/analysis_notebook_template.csv' WITH CSV HEADER;
\echo Dumping table analysis_software_source_code
\copy (SELECT analysis_software_source_code.* from analysis_software_source_code JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/analysis_software_source_code.csv' WITH CSV HEADER;
\echo Dumping table brain_atlas
\copy (SELECT brain_atlas.* from brain_atlas JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/brain_atlas.csv' WITH CSV HEADER;
\echo Dumping table brain_atlas_region
\copy (SELECT brain_atlas_region.* from brain_atlas_region JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/brain_atlas_region.csv' WITH CSV HEADER;
\echo Dumping table cell_composition
\copy (SELECT cell_composition.* from cell_composition JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/cell_composition.csv' WITH CSV HEADER;
\echo Dumping table cell_morphology
\copy (SELECT cell_morphology.* from cell_morphology JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/cell_morphology.csv' WITH CSV HEADER;
\echo Dumping table cell_morphology_protocol
\copy (SELECT cell_morphology_protocol.* from cell_morphology_protocol JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/cell_morphology_protocol.csv' WITH CSV HEADER;
\echo Dumping table circuit
\copy (SELECT circuit.* from circuit JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/circuit.csv' WITH CSV HEADER;
\echo Dumping table electrical_cell_recording
\copy (SELECT electrical_cell_recording.* from electrical_cell_recording JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/electrical_cell_recording.csv' WITH CSV HEADER;
\echo Dumping table electrical_recording
\copy (SELECT electrical_recording.* from electrical_recording JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/electrical_recording.csv' WITH CSV HEADER;
\echo Dumping table electrical_recording_stimulus
\copy (SELECT electrical_recording_stimulus.* from electrical_recording_stimulus JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/electrical_recording_stimulus.csv' WITH CSV HEADER;
\echo Dumping table em_cell_mesh
\copy (SELECT em_cell_mesh.* from em_cell_mesh JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/em_cell_mesh.csv' WITH CSV HEADER;
\echo Dumping table em_dense_reconstruction_dataset
\copy (SELECT em_dense_reconstruction_dataset.* from em_dense_reconstruction_dataset JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/em_dense_reconstruction_dataset.csv' WITH CSV HEADER;
\echo Dumping table emodel
\copy (SELECT emodel.* from emodel JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/emodel.csv' WITH CSV HEADER;
\echo Dumping table scientific_artifact
\copy (SELECT scientific_artifact.* from scientific_artifact JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/scientific_artifact.csv' WITH CSV HEADER;
\echo Dumping table experimental_bouton_density
\copy (SELECT experimental_bouton_density.* from experimental_bouton_density JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/experimental_bouton_density.csv' WITH CSV HEADER;
\echo Dumping table experimental_neuron_density
\copy (SELECT experimental_neuron_density.* from experimental_neuron_density JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/experimental_neuron_density.csv' WITH CSV HEADER;
\echo Dumping table experimental_synapses_per_connection
\copy (SELECT experimental_synapses_per_connection.* from experimental_synapses_per_connection JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/experimental_synapses_per_connection.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_model
\copy (SELECT ion_channel_model.* from ion_channel_model JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/ion_channel_model.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_recording
\copy (SELECT ion_channel_recording.* from ion_channel_recording JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/ion_channel_recording.csv' WITH CSV HEADER;
\echo Dumping table me_type_density
\copy (SELECT me_type_density.* from me_type_density JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/me_type_density.csv' WITH CSV HEADER;
\echo Dumping table memodel
\copy (SELECT memodel.* from memodel JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/memodel.csv' WITH CSV HEADER;
\echo Dumping table simulation
\copy (SELECT simulation.* from simulation JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/simulation.csv' WITH CSV HEADER;
\echo Dumping table simulation_campaign
\copy (SELECT simulation_campaign.* from simulation_campaign JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/simulation_campaign.csv' WITH CSV HEADER;
\echo Dumping table simulation_result
\copy (SELECT simulation_result.* from simulation_result JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/simulation_result.csv' WITH CSV HEADER;
\echo Dumping table single_neuron_simulation
\copy (SELECT single_neuron_simulation.* from single_neuron_simulation JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/single_neuron_simulation.csv' WITH CSV HEADER;
\echo Dumping table single_neuron_synaptome
\copy (SELECT single_neuron_synaptome.* from single_neuron_synaptome JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/single_neuron_synaptome.csv' WITH CSV HEADER;
\echo Dumping table single_neuron_synaptome_simulation
\copy (SELECT single_neuron_synaptome_simulation.* from single_neuron_synaptome_simulation JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/single_neuron_synaptome_simulation.csv' WITH CSV HEADER;
\echo Dumping table subject
\copy (SELECT subject.* from subject JOIN entity USING (id) WHERE entity.authorized_public IS true) TO '$WORKDIR/subject.csv' WITH CSV HEADER;
\echo Dumping table analysis_notebook_execution
\copy (SELECT analysis_notebook_execution.* from analysis_notebook_execution JOIN activity USING (id) WHERE activity.authorized_public IS true) TO '$WORKDIR/analysis_notebook_execution.csv' WITH CSV HEADER;
\echo Dumping table calibration
\copy (SELECT calibration.* from calibration JOIN activity USING (id) WHERE activity.authorized_public IS true) TO '$WORKDIR/calibration.csv' WITH CSV HEADER;
\echo Dumping table simulation_execution
\copy (SELECT simulation_execution.* from simulation_execution JOIN activity USING (id) WHERE activity.authorized_public IS true) TO '$WORKDIR/simulation_execution.csv' WITH CSV HEADER;
\echo Dumping table simulation_generation
\copy (SELECT simulation_generation.* from simulation_generation JOIN activity USING (id) WHERE activity.authorized_public IS true) TO '$WORKDIR/simulation_generation.csv' WITH CSV HEADER;
\echo Dumping table validation
\copy (SELECT validation.* from validation JOIN activity USING (id) WHERE activity.authorized_public IS true) TO '$WORKDIR/validation.csv' WITH CSV HEADER;
\echo Dumping table annotation
\copy (SELECT annotation.* FROM annotation JOIN entity AS t ON t.id=annotation.entity_id WHERE t.authorized_public IS true) TO '$WORKDIR/annotation.csv' WITH CSV HEADER;
\echo Dumping table asset
\copy (SELECT asset.* FROM asset JOIN entity AS t ON t.id=asset.entity_id WHERE t.authorized_public IS true) TO '$WORKDIR/asset.csv' WITH CSV HEADER;
\echo Dumping table contribution
\copy (SELECT contribution.* FROM contribution JOIN entity AS t ON t.id=contribution.entity_id WHERE t.authorized_public IS true) TO '$WORKDIR/contribution.csv' WITH CSV HEADER;
\echo Dumping table derivation
\copy (SELECT derivation.* FROM derivation JOIN entity AS t1 ON t1.id=derivation.used_id JOIN entity AS t2 ON t2.id=derivation.generated_id WHERE t1.authorized_public IS true AND t2.authorized_public IS true) TO '$WORKDIR/derivation.csv' WITH CSV HEADER;
\echo Dumping table etype_classification
\copy (SELECT etype_classification.* FROM etype_classification JOIN entity AS e ON e.id=etype_classification.entity_id WHERE etype_classification.authorized_public IS true AND e.authorized_public IS true) TO '$WORKDIR/etype_classification.csv' WITH CSV HEADER;
\echo Dumping table generation
\copy (SELECT generation.* FROM generation JOIN entity AS t1 ON t1.id=generation.generation_entity_id JOIN activity AS t2 ON t2.id=generation.generation_activity_id WHERE t1.authorized_public IS true AND t2.authorized_public IS true) TO '$WORKDIR/generation.csv' WITH CSV HEADER;
\echo Dumping table ion_channel_model__emodel
\copy (SELECT ion_channel_model__emodel.* FROM ion_channel_model__emodel JOIN entity AS t1 ON t1.id=ion_channel_model__emodel.ion_channel_model_id JOIN entity AS t2 ON t2.id=ion_channel_model__emodel.emodel_id WHERE t1.authorized_public IS true AND t2.authorized_public IS true) TO '$WORKDIR/ion_channel_model__emodel.csv' WITH CSV HEADER;
\echo Dumping table measurement_annotation
\copy (SELECT measurement_annotation.* FROM measurement_annotation JOIN entity AS t ON t.id=measurement_annotation.entity_id WHERE t.authorized_public IS true) TO '$WORKDIR/measurement_annotation.csv' WITH CSV HEADER;
\echo Dumping table measurement_item
\copy (SELECT measurement_item.* FROM measurement_item JOIN measurement_kind AS mk ON mk.id=measurement_item.measurement_kind_id JOIN measurement_annotation AS ma ON ma.id=mk.measurement_annotation_id JOIN entity AS e ON e.id=ma.entity_id WHERE e.authorized_public IS true) TO '$WORKDIR/measurement_item.csv' WITH CSV HEADER;
\echo Dumping table measurement_kind
\copy (SELECT measurement_kind.* FROM measurement_kind JOIN measurement_annotation AS ma ON ma.id=measurement_kind.measurement_annotation_id JOIN entity AS e ON e.id=ma.entity_id WHERE e.authorized_public IS true) TO '$WORKDIR/measurement_kind.csv' WITH CSV HEADER;
\echo Dumping table measurement_record
\copy (SELECT measurement_record.* FROM measurement_record JOIN entity AS t ON t.id=measurement_record.entity_id WHERE t.authorized_public IS true) TO '$WORKDIR/measurement_record.csv' WITH CSV HEADER;
\echo Dumping table memodel_calibration_result
\copy (SELECT memodel_calibration_result.* FROM memodel_calibration_result JOIN entity AS e1 ON e1.id=memodel_calibration_result.id JOIN entity AS e2 ON e2.id=memodel_calibration_result.calibrated_entity_id WHERE e1.authorized_public IS true AND e2.authorized_public IS true) TO '$WORKDIR/memodel_calibration_result.csv' WITH CSV HEADER;
\echo Dumping table mtype_classification
\copy (SELECT mtype_classification.* FROM mtype_classification JOIN entity AS e ON e.id=mtype_classification.entity_id WHERE mtype_classification.authorized_public IS true AND e.authorized_public IS true) TO '$WORKDIR/mtype_classification.csv' WITH CSV HEADER;
\echo Dumping table scientific_artifact_external_url_link
\copy (SELECT scientific_artifact_external_url_link.* FROM scientific_artifact_external_url_link JOIN entity AS t ON t.id=scientific_artifact_external_url_link.scientific_artifact_id WHERE t.authorized_public IS true) TO '$WORKDIR/scientific_artifact_external_url_link.csv' WITH CSV HEADER;
\echo Dumping table scientific_artifact_publication_link
\copy (SELECT scientific_artifact_publication_link.* FROM scientific_artifact_publication_link JOIN entity AS t ON t.id=scientific_artifact_publication_link.scientific_artifact_id WHERE t.authorized_public IS true) TO '$WORKDIR/scientific_artifact_publication_link.csv' WITH CSV HEADER;
\echo Dumping table usage
\copy (SELECT usage.* FROM usage JOIN entity AS t1 ON t1.id=usage.usage_entity_id JOIN activity AS t2 ON t2.id=usage.usage_activity_id WHERE t1.authorized_public IS true AND t2.authorized_public IS true) TO '$WORKDIR/usage.csv' WITH CSV HEADER;
\echo Dumping table validation_result
\copy (SELECT validation_result.* FROM validation_result JOIN entity AS e1 ON e1.id=validation_result.id JOIN entity AS e2 ON e2.id=validation_result.validated_entity_id WHERE e1.authorized_public IS true AND e2.authorized_public IS true) TO '$WORKDIR/validation_result.csv' WITH CSV HEADER;
COMMIT;
EOF

echo "Building archive..."
tar -czf "$DUMP_ARCHIVE" -C "$WORKDIR" .

echo "All done."
