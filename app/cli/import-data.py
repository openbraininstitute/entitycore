import argparse
import glob
import json
import os
import sys

import sqlalchemy
from tqdm import tqdm

from app.cli import curate, utils
from app.models import (
    agent,
    annotation,
    base,
    code,
    density,
    emodel,
    memodel,
    mesh,
    morphology,
    single_cell_experimental_trace,
    single_neuron_simulation,
)
from app.models.base import SessionLocal


def get_or_create_annotation_body(annotation_body, db):
    annotation_body = curate.curate_annotation_body(annotation_body)
    annotation_types = {
        "EType": annotation.ETypeAnnotationBody,
        "MType": annotation.MTypeAnnotationBody,
        "DataMaturity": annotation.DataMaturityAnnotationBody,
        "DataScope": None,
    }
    annotation_type_list = annotation_body["@type"]
    intersection = [
        value for value in annotation_type_list if value in annotation_types
    ]

    assert (
        len(intersection) == 1
    ), f"Unknown annotation body type {annotation_body['@type']}"
    db_annotation = annotation_types[intersection[0]]
    # TODO manage datascope
    if db_annotation is None:
        return None
    ab = (
        db.query(db_annotation)
        .filter(db_annotation.pref_label == annotation_body["label"])
        .first()
    )
    if not ab:
        if db_annotation is annotation.MTypeAnnotationBody:
            raise ValueError(f"Missing mtype in annotation body {annotation_body}")
        ab = db_annotation(pref_label=annotation_body["label"])
        db.add(ab)
        db.commit()
    return ab.id


def import_licenses(data, db):
    data.append(
        {
            "@id": "https://bbp.epfl.ch/neurosciencegraph/data/licenses/97521f71-605d-4f42-8f1b-c37e742a30b",
            "label": "undefined",
            "description": "undefined",
        }
    )
    data.append(
        {
            "@id": "https://bbp.epfl.ch/neurosciencegraph/data/licenses/97521f71-605d-4f42-8f1b-c37e742a30bf",
            "label": "undefined",
            "description": "undefined",
        }
    )
    for license in data:
        db_license = (
            db.query(base.License).filter(base.License.name == license["@id"]).first()
        )
        if db_license:
            continue
        try:
            db_license = base.License(
                name=license["@id"],
                label=license["label"],
                description=license["description"],
                legacy_id=[license["@id"]],
            )

            db.add(db_license)
            db.commit()
        except Exception as e:
            print(e)
            print(license)
            raise e


def _import_annotation_body(data, db_type_, db):
    for class_elem in tqdm(data):
        if db_type_ == annotation.ETypeAnnotationBody:
            class_elem = curate.curate_etype(class_elem)
        db_elem = (
            db.query(db_type_)
            .filter(db_type_.pref_label == class_elem["label"])
            .first()
        )
        if db_elem:
            assert db_elem.definition == class_elem.get("definition", "")
            assert db_elem.alt_label == class_elem.get("prefLabel", "")
            continue
        db_elem = db_type_(
            pref_label=class_elem["label"],
            definition=class_elem.get("definition", ""),
            alt_label=class_elem.get("prefLabel", ""),
            legacy_id=[class_elem["@id"]],
        )
        db.add(db_elem)
        db.commit()


def import_mtype_annotation_body(data, db):
    # Check if the annotation body already exists in the database
    data.append(
        {
            "label": "Inhibitory neuron",
            "definition": "Inhibitory neuron",
            "prefLabel": "Inhibitory neuron",
            "@id": "https://bbp.epfl.ch/neurosciencegraph/data/annotation/mtype/Inhibitoryneuron",
        }
    )
    data.append(
        {
            "label": "Excitatory neuron",
            "definition": "Excitatory neuron",
            "prefLabel": "Excitatory neuron",
            "@id": "https://bbp.epfl.ch/neurosciencegraph/data/annotation/mtype/Excitatoryneuron",
        }
    )
    _import_annotation_body(data, annotation.MTypeAnnotationBody, db)


def import_etype_annotation_body(data, db):
    _import_annotation_body(data, annotation.ETypeAnnotationBody, db)


def import_agents(data_list, db):
    data_list.append(
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/ikilic",
            "@type": "Person",
            "givenName": "Ilkan",
            "familyName": "Kilic",
        }
    )
    # TODO: find out who that is.
    data_list.append(
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/harikris",
            "@type": "Person",
            "givenName": "h",
            "familyName": "arikris",
        }
    )
    data_list.append(
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/ricardi",
            "@type": "Person",
            "givenName": "Nicolo",
            "familyName": "Ricardi",
        }
    )
    data_list.append(
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/akkaufma",
            "@type": "Person",
            "givenName": "Anna-Kristin",
            "familyName": "Kaufmann",
        }
    )
    data_list.append(
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/gbarrios",
            "@type": "Person",
            "givenName": "Gil",
            "familyName": "Barrios",
        }
    )
    data_list.append(
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/okeeva",
            "@type": "Person",
            "givenName": "Ayima",
            "familyName": "Okeeva",
        }
    )
    for data in data_list:
        if "Person" in data["@type"]:
            legacy_id = data["@id"]
            db_agent = utils._find_by_legacy_id(legacy_id, agent.Person, db)
            if not db_agent:
                try:
                    data = curate.curate_person(data)
                    givenName = data["givenName"]
                    familyName = data["familyName"]
                    label = f"{givenName} {familyName}"
                    db_agent = (
                        db.query(agent.Person)
                        .filter(
                            agent.Person.givenName == givenName,
                            agent.Person.familyName == familyName,
                        )
                        .first()
                    )
                    if db_agent:
                        ll = db_agent.legacy_id.copy()
                        ll.append(legacy_id)
                        db_agent.legacy_id = ll

                        db.commit()
                    else:
                        db_agent = agent.Person(
                            legacy_id=[legacy_id],
                            givenName=data["givenName"],
                            familyName=data["familyName"],
                            pref_label=label,
                        )
                        db.add(db_agent)
                        db.commit()
                except Exception as e:
                    print("Error importing person: ", data)
                    print(e)
        elif "Organization" in data["@type"]:
            legacy_id = data["@id"]
            db_agent = utils._find_by_legacy_id(legacy_id, agent.Organization, db)
            if not db_agent:
                try:
                    name = data["name"]
                    db_agent = (
                        db.query(agent.Organization)
                        .filter(agent.Organization.pref_label == name)
                        .first()
                    )
                    if db_agent:
                        ll = db_agent.legacy_id.copy()
                        ll.append(legacy_id)
                        db_agent.legacy_id = ll

                        db.commit()
                    else:
                        db_agent = agent.Organization(
                            legacy_id=[legacy_id],
                            pref_label=data.get("name"),
                            alternative_name=data.get("alternativeName", ""),
                        )
                        db.add(db_agent)
                        db.commit()
                except Exception as e:
                    print("Error importing organization: ", data)
                    print(e)


def import_single_neuron_simulation(data, db):
    possible_data = [elem for elem in data if "SingleNeuronSimulation" in elem["@type"]]
    if not possible_data:
        return
    for data in tqdm(possible_data):
        legacy_id = data["@id"]
        rm = utils._find_by_legacy_id(
            legacy_id, single_neuron_simulation.SingleNeuronSimulation, db
        )
        if not rm:
            brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)
            me_model_lid = data.get("used", {}).get("@id", None)
            me_model = utils._find_by_legacy_id(me_model_lid, memodel.MEModel, db)
            rm = single_neuron_simulation.SingleNeuronSimulation(
                legacy_id=[legacy_id],
                name=data.get("name", None),
                description=data.get("description", None),
                seed=data.get("seed", None),
                injectionLocation=data.get("injectionLocation", None),
                recordingLocation=data.get("recordingLocation", None),
                me_model_id=me_model.id,
                brain_region_id=brain_region_id,
                createdBy_id=created_by_id,
                updatedBy_id=updated_by_id,
            )
            db.add(rm)
            db.commit()


def get_or_create_annotation(annotation_, reconstruction_morphology_id, db):
    annotation_body_id = get_or_create_annotation_body(annotation_["hasBody"], db)
    if not annotation_body_id:
        return None
    db_annotation = annotation.Annotation(
        entity_id=reconstruction_morphology_id,
        note=annotation_.get("note", None),
        annotation_body_id=annotation_body_id,
    )
    db.add(db_annotation)
    db.commit()
    return db_annotation.id


def import_analysis_software_source_code(data, db):
    possible_data = [
        data for data in data if data["@type"] == "AnalysisSoftwareSourceCode"
    ]
    if not possible_data:
        return
    for data in tqdm(possible_data):
        legacy_id = data["@id"]
        rm = utils._find_by_legacy_id(legacy_id, code.AnalysisSoftwareSourceCode, db)
        if not rm:
            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)
            db_code = code.AnalysisSoftwareSourceCode(
                legacy_id=[legacy_id],
                name=data.get("name", ""),
                description=data.get("description", ""),
                createdBy_id=created_by_id,
                updatedBy_id=updated_by_id,
                branch=data.get("branch", ""),
                commit=data.get("commit", ""),
                codeRepository=data.get("codeRepository", ""),
                command=data.get("command", ""),
                subdirectory=data.get("subdirectory", ""),
                targetEntity=data.get("targetEntity", ""),
                programmingLanguage=data.get("programmingLanguage", ""),
                runtimePlatform=data.get("runtimePlatform", ""),
                version=data.get("version", ""),
            )
            db.add(db_code)
            db.commit()


def import_me_models(data, db):
    def is_memodel(data):
        types = data["@type"]
        if isinstance(types, list):
            return "MEModel" in types or "https://neuroshapes.org/MEModel" in types
        return "MEModel" == types or "https://neuroshapes.org/MEModel" == types

    possible_data = [data for data in data if is_memodel(data)]
    if not possible_data:
        return
    for data in tqdm(possible_data):
        legacy_id = data["@id"]
        rm = utils._find_by_legacy_id(legacy_id, memodel.MEModel, db)
        if not rm:
            brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)
            # TO DO: add species and strain mixin ?
            # species_id, strain_id = utils.get_species_mixin(data, db)
            rm = memodel.MEModel(
                legacy_id=[legacy_id],
                name=data.get("name", None),
                description=data.get("description", None),
                validated=data.get("validated", None),
                status=data.get("status", None),
                brain_location=brain_location,
                brain_region_id=brain_region_id,
                createdBy_id=created_by_id,
                updatedBy_id=updated_by_id,
                # species_id=species_id,
                # strain_id=strain_id
            )
            db.add(rm)
            db.commit()
            # get_or_create_annotation(data, rm.id, db)


def import_e_models(data, db):
    def is_emodel(data):
        types = data["@type"]
        if isinstance(types, list):
            return "EModel" in types
        return "EModel" == types

    possible_data = [data for data in data if is_emodel(data)]
    if not possible_data:
        return
    for data in tqdm(possible_data):
        legacy_id = data["@id"]
        db_item = utils._find_by_legacy_id(legacy_id, emodel.EModel, db)
        if not db_item:
            brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            species_id, strain_id = utils.get_species_mixin(data, db)
            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)
            db_item = emodel.EModel(
                legacy_id=[legacy_id],
                name=data.get("name", None),
                description=data.get("description", None),
                score=data.get("score", None),
                seed=data.get("seed", None),
                iteration=data.get("iteration", None),
                eModel=data.get("eModel", None),
                eType=data.get("eType", None),
                brain_location=brain_location,
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=strain_id,
                createdBy_id=created_by_id,
                updatedBy_id=updated_by_id,
            )

            db.add(db_item)
            db.commit()
            utils.import_contribution(data, db_item.id, db)
            annotations = data.get("annotation", [])
            if isinstance(annotations, dict):
                annotations = [annotations]
            for annotation in annotations:
                get_or_create_annotation(annotation, db_item.id, db)


def import_brain_region_meshes(data, db):
    possible_data = [data for data in data if "BrainParcellationMesh" in data["@type"]]
    possible_data = [
        data
        for data in possible_data
        if data.get("atlasRelease").get("tag", None) == "v1.1.0"
    ]
    if not possible_data:
        return
    for data in tqdm(possible_data):
        legacy_id = data["@id"]
        rm = utils._find_by_legacy_id(legacy_id, mesh.Mesh, db)
        if not rm:
            _, brain_region_id = utils.get_brain_location_mixin(data, db)
            content_url = data.get("distribution").get("contentUrl")
            db_item = mesh.Mesh(
                legacy_id=[legacy_id],
                brain_region_id=brain_region_id,
                content_url=content_url,
            )
            db.add(db_item)
            db.commit()


def import_traces(data_list, db):
    possible_data = [
        data for data in data_list if "SingleCellExperimentalTrace" in data["@type"]
    ]
    if not possible_data:
        return
    for data in tqdm(possible_data):
        legacy_id = data["@id"]
        rm = utils._find_by_legacy_id(
            legacy_id, single_cell_experimental_trace.SingleCellExperimentalTrace, db
        )
        if not rm:
            data = curate.curate_trace(data)
            description = data.get("description", None)
            name = data.get("name", None)
            brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            license_id = utils.get_license_mixin(data, db)
            species_id, strain_id = utils.get_species_mixin(data, db)
            db_item = single_cell_experimental_trace.SingleCellExperimentalTrace(
                legacy_id=[data.get("@id", None)],
                name=name,
                description=description,
                brain_location=brain_location,
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=strain_id,
                license_id=license_id,
            )
            db.add(db_item)
            db.commit()
            db.refresh(db_item)
            utils.import_contribution(data, db_item.id, db)
            annotations = data.get("annotation", [])
            if isinstance(annotations, dict):
                annotations = [annotations]
            for annotation in annotations:
                get_or_create_annotation(annotation, db_item.id, db)


def import_morphologies(data_list, db):
    possible_data = [
        data for data in data_list if "ReconstructedNeuronMorphology" in data["@type"]
    ]
    if not possible_data:
        return
    for data in tqdm(possible_data):
        legacy_id = data["@id"]
        rm = utils._find_by_legacy_id(
            legacy_id, morphology.ReconstructionMorphology, db
        )
        if not rm:
            description = data.get("description", None)
            name = data.get("name", None)
            brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            license_id = utils.get_license_mixin(data, db)
            species_id, strain_id = utils.get_species_mixin(data, db)
            db_reconstruction_morphology = morphology.ReconstructionMorphology(
                legacy_id=[data.get("@id", None)],
                name=name,
                description=description,
                brain_location=brain_location,
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=strain_id,
                license_id=license_id,
            )
            db.add(db_reconstruction_morphology)
            db.commit()
            db.refresh(db_reconstruction_morphology)
            utils.import_contribution(data, db_reconstruction_morphology.id, db)
            annotations = data.get("annotation", [])
            if isinstance(annotations, dict):
                annotations = [annotations]
            for annotation in annotations:
                get_or_create_annotation(
                    annotation, db_reconstruction_morphology.id, db
                )


def import_morphology_feature_annotations(data_list, db):
    possible_data = [
        data
        for data in data_list
        if "NeuronMorphologyFeatureAnnotation" in data["@type"]
    ]
    if not possible_data:
        return
    for data in tqdm(possible_data):
        try:
            legacy_id = data.get("hasTarget", {}).get("hasSource", {}).get("@id", None)
            if not legacy_id:
                print(
                    "Skipping morphology feature annotation due to missing legacy id."
                )
                continue
            rm = utils._find_by_legacy_id(
                legacy_id, morphology.ReconstructionMorphology, db
            )
            if not rm:
                print("skipping morphology that is not imported")
                continue
            all_measurements = []
            for measurement in data.get("hasBody", []):
                serie = measurement.get("value", {}).get("series", [])
                if isinstance(serie, dict):
                    serie = [serie]
                measurement_serie = [
                    morphology.MorphologyMeasurementSerieElement(
                        name=serie_elem.get("statistic", None),
                        value=serie_elem.get("value", None),
                    )
                    for serie_elem in serie
                ]

                all_measurements.append(
                    morphology.MorphologyMeasurement(
                        measurement_of=measurement.get("isMeasurementOf", {}).get(
                            "label", None
                        ),
                        measurement_serie=measurement_serie,
                    )
                )

            db_morphology_feature_annotation = morphology.MorphologyFeatureAnnotation(
                reconstruction_morphology_id=rm.id
            )
            db_morphology_feature_annotation.measurements = all_measurements
            db.add(db_morphology_feature_annotation)
            db.commit()
            db.refresh(db_morphology_feature_annotation)
        except sqlalchemy.exc.IntegrityError:
            # TODO: investigate if what is actually happening
            print("2 annotations for a morphology ignoring")
            db.rollback()
            continue
        except Exception as e:
            print(f"Error: {e}")
            print(data)


def import_experimental_neuron_densities(data_list, db):
    _import_experimental_densities(
        data_list,
        db,
        "ExperimentalNeuronDensity",
        density.ExperimentalNeuronDensity,
        curate.default_curate,
    )


def import_experimental_bouton_densities(data_list, db):
    _import_experimental_densities(
        data_list,
        db,
        "ExperimentalBoutonDensity",
        density.ExperimentalBoutonDensity,
        curate.default_curate,
    )


def import_experimental_synapses_per_connection(data_list, db):
    _import_experimental_densities(
        data_list,
        db,
        "ExperimentalSynapsesPerConnection",
        density.ExperimentalSynapsesPerConnection,
        curate.curate_synapses_per_connections,
    )


def _import_experimental_densities(
    data_list, db, schema_type, model_type, curate_function
):
    possible_data = [data for data in data_list if schema_type in data["@type"]]
    if not possible_data:
        return
    for data in tqdm(possible_data):
        data = curate_function(data)
        legacy_id = data["@id"]
        db_element = utils._find_by_legacy_id(legacy_id, model_type, db)
        if not db_element:
            license_id = utils.get_license_mixin(data, db)
            species_id, strain_id = utils.get_species_mixin(data, db)
            brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            _createdBy_id, _updatedBy_id = utils.get_agent_mixin(data, db)
            db_element = model_type(
                legacy_id=[legacy_id],
                name=data.get("name", None),
                description=data.get("description", None),
                species_id=species_id,
                strain_id=strain_id,
                license_id=license_id,
                brain_location=brain_location,
                brain_region_id=brain_region_id,
                createdBy_id=_createdBy_id,
                updatedBy_id=_updatedBy_id,
            )
            db.add(db_element)
            db.commit()
            utils.import_contribution(data, db_element.id, db)


def main():
    parser = argparse.ArgumentParser(description="Import data script")
    parser.add_argument("--db", required=True, help="Database parameter")
    parser.add_argument("--input_dir", required=True, help="Input directory path")

    args = parser.parse_args()

    if not os.path.exists(args.input_dir):
        print(f"Error: Input directory '{args.input_dir}' does not exist")
        sys.exit(1)

    if not os.path.exists(args.db):
        print(f"Error: Database file '{args.db}' does not exist")
        sys.exit(1)

    db = SessionLocal()

    all_files = glob.glob(os.path.join(args.input_dir, "*", "*", "*.json"))
    print("importing agents")
    for file_path in all_files:
        with open(file_path) as f:
            data = json.load(f)
            import_agents(data, db)
    print("import licenses")
    with open(
        os.path.join(args.input_dir, "bbp", "licenses", "provEntity.json"),
    ) as f:
        data = json.load(f)
        import_licenses(data, db)
    print("import mtype annotations")
    with open(
        os.path.join(
            args.input_dir, "neurosciencegraph", "datamodels", "owlClass.json"
        ),
    ) as f:
        data = json.load(f)
        possible_data = [
            data for data in data if "nsg:MType" in data.get("subClassOf", {})
        ]
        import_mtype_annotation_body(possible_data, db)

    print("import etype annotations")
    with open(
        os.path.join(
            args.input_dir, "neurosciencegraph", "datamodels", "owlClass.json"
        ),
    ) as f:
        data = json.load(f)
        possible_data = [
            data for data in data if "nsg:EType" in data.get("subClassOf", {})
        ]
        import_etype_annotation_body(possible_data, db)

    l_imports = [
        {"AnalysisSoftwareSourceCode": import_analysis_software_source_code},
        {"eModels": import_e_models},
        {"meshes": import_brain_region_meshes},
        {"morphologies": import_morphologies},
        {"morphologyFeatureAnnotations": import_morphology_feature_annotations},
        {"experimentalNeuronDensities": import_experimental_neuron_densities},
        {"experimentalBoutonDensities": import_experimental_bouton_densities},
        {
            "experimentalSynapsesPerConnections": import_experimental_synapses_per_connection
        },
        {"traces": import_traces},
        {"meModels": import_me_models},
        {"SingleNeuronSimulation": import_single_neuron_simulation},
    ]
    for l_import in l_imports:
        for label, action in l_import.items():
            print(f"importing {label}")
            for file_path in all_files:
                with open(file_path) as f:
                    data = json.load(f)
                    action(data, db)


if __name__ == "__main__":
    main()
