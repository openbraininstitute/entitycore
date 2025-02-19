import datetime
import glob
import json
import os
from contextlib import closing
from collections import defaultdict

import click
import sqlalchemy as sa
from tqdm import tqdm
from pydantic import UUID4

from app.cli import curate, utils
from app.db.model import (
    AnalysisSoftwareSourceCode,
    Annotation,
    BrainRegion,
    DataMaturityAnnotationBody,
    EModel,
    ETypeAnnotationBody,
    ExperimentalBoutonDensity,
    ExperimentalNeuronDensity,
    ExperimentalSynapsesPerConnection,
    License,
    MEModel,
    Mesh,
    MorphologyFeatureAnnotation,
    MorphologyMeasurement,
    MorphologyMeasurementSerieElement,
    MTypeAnnotationBody,
    Organization,
    Person,
    ReconstructionMorphology,
    SingleCellExperimentalTrace,
    SingleNeuronSimulation,
)
from app.db.session import configure_database_session_manager


REQUIRED_PATH = click.Path(exists=True, readable=True, dir_okay=False, resolve_path=True)
REQUIRED_PATH_DIR = click.Path(
    exists=True, readable=True, file_okay=False, dir_okay=True, resolve_path=True
)


def get_or_create_annotation_body(annotation_body, db):
    annotation_body = curate.curate_annotation_body(annotation_body)
    annotation_types = {
        "EType": ETypeAnnotationBody,
        "MType": MTypeAnnotationBody,
        "DataMaturity": DataMaturityAnnotationBody,
        "DataScope": None,
    }
    annotation_type_list = annotation_body["@type"]
    intersection = [value for value in annotation_type_list if value in annotation_types]

    assert len(intersection) == 1, f"Unknown annotation body type {annotation_body['@type']}"
    db_annotation = annotation_types[intersection[0]]
    # TODO manage datascope
    if db_annotation is None:
        return None
    ab = (
        db.query(db_annotation).filter(db_annotation.pref_label == annotation_body["label"]).first()
    )
    if not ab:
        if db_annotation is MTypeAnnotationBody:
            msg = f"Missing mtype in annotation body {annotation_body}"
            raise ValueError(msg)
        ab = db_annotation(pref_label=annotation_body["label"])
        db.add(ab)
        db.commit()
    return ab.id


def import_licenses(data, db):
    for license in data:
        db_license = db.query(License).filter(License.name == license["@id"]).first()
        if db_license:
            continue

        try:
            createdAt, updatedAt = utils.get_created_and_updated(license)

            db_license = License(
                name=license["@id"],
                label=license["label"],
                description=license["description"],
                legacy_id=[license["@id"]],
                creation_date=createdAt,
                update_date=updatedAt,
            )

            db.add(db_license)
            db.commit()
        except Exception as e:
            print(f"Error creating license: {e!r}")
            print(license)
            raise


def _import_annotation_body(data, db_type_, db):
    for class_elem in tqdm(data):
        if db_type_ == ETypeAnnotationBody:
            class_elem = curate.curate_etype(class_elem)

        db_elem = db.query(db_type_).filter(db_type_.pref_label == class_elem["label"]).first()

        if db_elem:
            assert db_elem.definition == class_elem.get("definition", "")
            assert db_elem.alt_label == class_elem.get("prefLabel", "")

            continue

        createdAt, updatedAt = utils.get_created_and_updated(class_elem)

        db_elem = db_type_(
            pref_label=class_elem["label"],
            definition=class_elem.get("definition", ""),
            alt_label=class_elem.get("prefLabel", ""),
            legacy_id=[class_elem["@id"]],
            creation_date=createdAt,
            update_date=updatedAt,
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
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        }
    )
    data.append(
        {
            "label": "Excitatory neuron",
            "definition": "Excitatory neuron",
            "prefLabel": "Excitatory neuron",
            "@id": "https://bbp.epfl.ch/neurosciencegraph/data/annotation/mtype/Excitatoryneuron",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        }
    )
    _import_annotation_body(data, MTypeAnnotationBody, db)


def import_etype_annotation_body(data, db):
    _import_annotation_body(data, ETypeAnnotationBody, db)


def import_agents(data_list, db):
    for data in data_list:
        if "Person" in data["@type"]:
            legacy_id = data["@id"]
            db_agent = utils._find_by_legacy_id(legacy_id, Person, db)
            if not db_agent:
                try:
                    data = curate.curate_person(data)
                    givenName = data["givenName"]
                    familyName = data["familyName"]
                    label = f"{givenName} {familyName}"
                    db_agent = (
                        db.query(Person)
                        .filter(
                            Person.givenName == givenName,
                            Person.familyName == familyName,
                        )
                        .first()
                    )
                    if db_agent:
                        ll = db_agent.legacy_id.copy()
                        ll.append(legacy_id)
                        db_agent.legacy_id = ll

                        db.commit()
                    else:
                        createdAt, updatedAt = utils.get_created_and_updated(data)
                        db_agent = Person(
                            legacy_id=[legacy_id],
                            givenName=data["givenName"],
                            familyName=data["familyName"],
                            pref_label=label,
                            creation_date=createdAt,
                            update_date=updatedAt,
                        )
                        db.add(db_agent)
                        db.commit()
                except Exception as e:
                    print("Error importing person: ", data)
                    print(f"{e!r}")
        elif "Organization" in data["@type"]:
            legacy_id = data["@id"]
            db_agent = utils._find_by_legacy_id(legacy_id, Organization, db)
            if not db_agent:
                try:
                    name = data["name"]
                    db_agent = (
                        db.query(Organization).filter(Organization.pref_label == name).first()
                    )
                    if db_agent:
                        ll = db_agent.legacy_id.copy()
                        ll.append(legacy_id)
                        db_agent.legacy_id = ll

                        db.commit()
                    else:
                        createdAt, updatedAt = utils.get_created_and_updated(data)
                        db_agent = Organization(
                            legacy_id=[legacy_id],
                            pref_label=data.get("name"),
                            alternative_name=data.get("alternativeName", ""),
                            creation_date=createdAt,
                            update_date=updatedAt,
                        )
                        db.add(db_agent)
                        db.commit()
                except Exception as e:
                    print("Error importing organization: ", data)
                    print(f"{e!r}")


def import_single_neuron_simulation(data, db, file_path, project_id):
    possible_data = [elem for elem in data if "SingleNeuronSimulation" in elem["@type"]]
    if not possible_data:
        return
    for data in tqdm(possible_data):
        legacy_id = data["@id"]
        rm = utils._find_by_legacy_id(legacy_id, SingleNeuronSimulation, db)
        if not rm:
            _brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)
            me_model_lid = data.get("used", {}).get("@id", None)
            me_model = utils._find_by_legacy_id(me_model_lid, MEModel, db)
            rm = SingleNeuronSimulation(
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
                authorized_project_id=project_id,
            )
            db.add(rm)
            db.commit()


def get_or_create_annotation(annotation_, reconstruction_morphology_id, db):
    annotation_body_id = get_or_create_annotation_body(annotation_["hasBody"], db)
    if not annotation_body_id:
        return None
    db_annotation = Annotation(
        entity_id=reconstruction_morphology_id,
        note=annotation_.get("note", None),
        annotation_body_id=annotation_body_id,
    )
    db.add(db_annotation)
    db.commit()
    return db_annotation.id


def import_analysis_software_source_code(data, db, file_path, project_id):
    possible_data = [data for data in data if data["@type"] == "AnalysisSoftwareSourceCode"]
    if not possible_data:
        return
    for data in tqdm(possible_data):
        legacy_id = data["@id"]
        rm = utils._find_by_legacy_id(legacy_id, AnalysisSoftwareSourceCode, db)
        if not rm:
            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)
            createdAt, updatedAt = utils.get_created_and_updated(data)

            db_code = AnalysisSoftwareSourceCode(
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
                creation_date=createdAt,
                update_date=updatedAt,
                authorized_project_id=project_id,
            )
            db.add(db_code)
            db.commit()


def import_me_models(data, db, file_path, project_id):
    def is_memodel(data):
        types = data["@type"]
        if isinstance(types, list):
            return "MEModel" in types or "https://neuroshapes.org/MEModel" in types
        return types in {"MEModel", "https://neuroshapes.org/MEModel"}

    possible_data = [data for data in data if is_memodel(data)]
    if not possible_data:
        return
    for data in tqdm(possible_data):
        legacy_id = data["@id"]
        rm = utils._find_by_legacy_id(legacy_id, MEModel, db)
        if not rm:
            brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)
            createdAt, updatedAt = utils.get_created_and_updated(data)
            # TO DO: add species and strain mixin ?
            # species_id, strain_id = utils.get_species_mixin(data, db)
            rm = MEModel(
                legacy_id=[legacy_id],
                name=data.get("name", None),
                description=data.get("description", None),
                validated=data.get("validated", None),
                status=data.get("status", None),
                brain_location=brain_location,
                brain_region_id=brain_region_id,
                createdBy_id=created_by_id,
                updatedBy_id=updated_by_id,
                authorized_project_id=project_id,
                # species_id=species_id,
                # strain_id=strain_id
                creation_date=createdAt,
                update_date=updatedAt,
            )
            db.add(rm)
            db.commit()
            # get_or_create_annotation(data, rm.id, db)


def import_e_models(data, db, file_path, project_id):
    def is_emodel(data):
        types = data["@type"]
        if isinstance(types, list):
            return "EModel" in types
        return types == "EModel"

    possible_data = [data for data in data if is_emodel(data)]

    if not possible_data:
        return

    for data in tqdm(possible_data):
        legacy_id = data["@id"]
        db_item = utils._find_by_legacy_id(legacy_id, EModel, db)
        if not db_item:
            brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            species_id, strain_id = utils.get_species_mixin(data, db)
            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)
            createdAt, updatedAt = utils.get_created_and_updated(data)

            db_item = EModel(
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
                creation_date=createdAt,
                update_date=updatedAt,
                authorized_project_id=project_id,
            )

            db.add(db_item)
            db.commit()
            utils.import_contribution(data, db_item.id, db)

            annotations = data.get("annotation", [])

            if isinstance(annotations, dict):
                annotations = [annotations]
            for annotation in annotations:
                get_or_create_annotation(annotation, db_item.id, db)


def import_brain_region_meshes(data, db, file_path, project_id):
    possible_data = [data for data in data if "BrainParcellationMesh" in data["@type"]]
    possible_data = [
        data for data in possible_data if data.get("atlasRelease").get("tag", None) == "v1.1.0"
    ]
    if not possible_data:
        return
    for data in tqdm(possible_data):
        legacy_id = data["@id"]
        rm = utils._find_by_legacy_id(legacy_id, Mesh, db)
        if not rm:
            _, brain_region_id = utils.get_brain_location_mixin(data, db)

            createdAt, updatedAt = utils.get_created_and_updated(data)

            content_url = data.get("distribution").get("contentUrl")

            db_item = Mesh(
                legacy_id=[legacy_id],
                brain_region_id=brain_region_id,
                content_url=content_url,
                creation_date=createdAt,
                update_date=updatedAt,
                authorized_project_id=project_id,
            )
            db.add(db_item)
            db.commit()


def import_traces(data_list, db, file_path, project_id):
    possible_data = [data for data in data_list if "SingleCellExperimentalTrace" in data["@type"]]
    if not possible_data:
        return
    for data in tqdm(possible_data):
        legacy_id = data["@id"]
        rm = utils._find_by_legacy_id(legacy_id, SingleCellExperimentalTrace, db)
        if not rm:
            data = curate.curate_trace(data)

            brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            license_id = utils.get_license_mixin(data, db)
            species_id, strain_id = utils.get_species_mixin(data, db)
            createdAt, updatedAt = utils.get_created_and_updated(data)

            db_item = SingleCellExperimentalTrace(
                legacy_id=[data.get("@id", None)],
                name=data["name"],
                description=data["description"],
                brain_location=brain_location,
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=strain_id,
                license_id=license_id,
                creation_date=createdAt,
                update_date=updatedAt,
                authorized_project_id=project_id,
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


def import_morphologies(data_list, db, file_path, project_id):
    possible_data = [data for data in data_list if "ReconstructedNeuronMorphology" in data["@type"]]
    if not possible_data:
        return
    for data in tqdm(possible_data):
        legacy_id = data["@id"]
        rm = utils._find_by_legacy_id(legacy_id, ReconstructionMorphology, db)
        if not rm:
            brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            license_id = utils.get_license_mixin(data, db)
            species_id, strain_id = utils.get_species_mixin(data, db)
            createdAt, updatedAt = utils.get_created_and_updated(data)

            db_reconstruction_morphology = ReconstructionMorphology(
                legacy_id=[data.get("@id", None)],
                name=data["name"],
                description=data["description"],
                brain_location=brain_location,
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=strain_id,
                license_id=license_id,
                creation_date=createdAt,
                update_date=updatedAt,
                authorized_project_id=project_id,
            )

            db.add(db_reconstruction_morphology)
            db.commit()
            db.refresh(db_reconstruction_morphology)

            utils.import_contribution(data, db_reconstruction_morphology.id, db)
            annotations = data.get("annotation", [])
            if isinstance(annotations, dict):
                annotations = [annotations]
            for annotation in annotations:
                get_or_create_annotation(annotation, db_reconstruction_morphology.id, db)


def import_morphology_feature_annotations(data_list, db, file_path, project_id):
    annotations = defaultdict(list)
    missing_morphology = 0
    duplicate_annotation = 0
    for data in data_list:
        if "NeuronMorphologyFeatureAnnotation" not in data["@type"]:
            continue

        legacy_id = data.get("hasTarget", {}).get("hasSource", {}).get("@id", None)
        if not legacy_id:
            print("Skipping morphology feature annotation due to missing legacy id.")
            continue

        rm = utils._find_by_legacy_id(legacy_id, ReconstructionMorphology, db)
        if not rm:
            missing_morphology += 1
            continue

        all_measurements = []
        for measurement in data.get("hasBody", []):
            serie = measurement.get("value", {}).get("series", [])
            if isinstance(serie, dict):
                serie = [serie]

            measurement_serie = [
                MorphologyMeasurementSerieElement(
                    name=serie_elem.get("statistic", None),
                    value=serie_elem.get("value", None),
                )
                for serie_elem in serie
            ]

            all_measurements.append(
                MorphologyMeasurement(
                    measurement_of=measurement.get("isMeasurementOf", {}).get("label", None),
                    measurement_serie=measurement_serie,
                )
            )

        createdAt, updatedAt = utils.get_created_and_updated(data)

        annotations[rm.id].append(
            MorphologyFeatureAnnotation(
                reconstruction_morphology_id=rm.id,
                measurements=all_measurements,
                creation_date=createdAt,
                update_date=updatedAt,
            )
        )

    if not annotations:
        return

    already_registered = 0
    for rm_id, annotation in tqdm(annotations.items()):
        mfa = (
            db.query(MorphologyFeatureAnnotation)
            .filter(MorphologyFeatureAnnotation.reconstruction_morphology_id == rm_id)
            .first()
        )
        if mfa:
            already_registered += len(annotation)
            continue

        if len(annotation) > 1:
            duplicate_annotation += len(annotation) - 1

        # TODO:
        # JDC wants to look into why there are multiple annotations:
        # https://github.com/openbraininstitute/entitycore/pull/16#discussion_r1940740060
        data = annotation[0]

        try:
            db.add(data)
            db.commit()
            db.refresh(data)
        except Exception as e:
            print(f"Error: {e!r}")
            print(data)
            raise

    print(
        f"{file_path}: \n"
        f"    Annotations related to a morphology that isn't registered: {missing_morphology}\n",
        f"    Duplicate_annotation: {duplicate_annotation}\n",
        f"    Previously registered: {already_registered}\n",
        f"    Total Duplicate: {duplicate_annotation + already_registered}",
    )


def import_experimental_neuron_densities(data_list, db, file_path, project_id):
    _import_experimental_densities(
        data_list,
        db,
        "ExperimentalNeuronDensity",
        ExperimentalNeuronDensity,
        curate.default_curate,
        project_id,
    )


def import_experimental_bouton_densities(data_list, db, file_path, project_id):
    _import_experimental_densities(
        data_list,
        db,
        "ExperimentalBoutonDensity",
        ExperimentalBoutonDensity,
        curate.default_curate,
        project_id,
    )


def import_experimental_synapses_per_connection(data_list, db, file_path, project_id):
    _import_experimental_densities(
        data_list,
        db,
        "ExperimentalSynapsesPerConnection",
        ExperimentalSynapsesPerConnection,
        curate.curate_synapses_per_connections,
        project_id,
    )


def _import_experimental_densities(
    data_list, db, schema_type, model_type, curate_function, project_id
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
            createdBy_id, updatedBy_id = utils.get_agent_mixin(data, db)

            createdAt, updatedAt = utils.get_created_and_updated(data)

            db_element = model_type(
                legacy_id=[legacy_id],
                name=data.get("name", None),
                description=data.get("description", None),
                species_id=species_id,
                strain_id=strain_id,
                license_id=license_id,
                brain_location=brain_location,
                brain_region_id=brain_region_id,
                createdBy_id=createdBy_id,
                updatedBy_id=updatedBy_id,
                creation_date=createdAt,
                update_date=updatedAt,
                authorized_project_id=project_id,
            )
            db.add(db_element)
            db.commit()
            utils.import_contribution(data, db_element.id, db)


def _do_import(db, input_dir, project_id):
    all_files = sorted(glob.glob(os.path.join(input_dir, "*", "*", "*.json")))

    print("importing agents")
    import_agents(curate.default_agents(), db)
    for file_path in all_files:
        with open(file_path) as f:
            data = json.load(f)
            possible_data = [
                d for d in data if {"Person", "Organization"} & set(d.get("@type", {}))
            ]
            import_agents(possible_data, db)

    print("import licenses")
    import_licenses(curate.default_licenses(), db)
    with open(os.path.join(input_dir, "bbp", "licenses", "provEntity.json")) as f:
        data = json.load(f)
        import_licenses(data, db)

    print("import mtype annotations")
    with open(os.path.join(input_dir, "neurosciencegraph", "datamodels", "owlClass.json")) as f:
        data = json.load(f)
        possible_data = [d for d in data if "nsg:MType" in d.get("subClassOf", {})]
        import_mtype_annotation_body(possible_data, db)

    with open(os.path.join(input_dir, "neurosciencegraph", "datamodels", "owlClass.json")) as f:
        all_data = json.load(f)
        mtype_annotations, etype_annotations = [], []

        for data in all_data:
            sub_class = data.get("subClassOf", {})
            if "nsg:MType" in sub_class:
                mtype_annotations.append(data)
            elif "nsg:EType" in sub_class:
                etype_annotations.append(data)

        print("import mtype annotations")
        import_mtype_annotation_body(mtype_annotations, db)

        print("import etype annotations")
        import_etype_annotation_body(etype_annotations, db)

    l_imports = [
        {"AnalysisSoftwareSourceCode": import_analysis_software_source_code},
        {"eModels": import_e_models},
        {"meshes": import_brain_region_meshes},
        {"morphologies": import_morphologies},
        {"morphologyFeatureAnnotations": import_morphology_feature_annotations},
        {"experimentalNeuronDensities": import_experimental_neuron_densities},
        {"experimentalBoutonDensities": import_experimental_bouton_densities},
        {"experimentalSynapsesPerConnections": import_experimental_synapses_per_connection},
        {"traces": import_traces},
        {"meModels": import_me_models},
        {"SingleNeuronSimulation": import_single_neuron_simulation},
    ]
    for l_import in l_imports:
        for label, action in l_import.items():
            print(f"importing {label}")
            for file_path in all_files:
                print(f"   {file_path}")
                with open(file_path) as f:
                    data = json.load(f)
                    action(data, db, file_path=file_path, project_id=project_id)


def _analyze() -> None:
    with (
        closing(configure_database_session_manager()) as database_session_manager,
        database_session_manager.session() as db,
    ):
        # running in a transaction although it's not needed
        db.execute(sa.text("ANALYZE"))


@click.group()
def cli():
    """Main CLI group."""


@cli.command()
def analyze():
    """Update statistics used by the query planner."""
    _analyze()


@cli.command()
@click.argument("input-dir", type=REQUIRED_PATH_DIR)
@click.option(
    "--project-id",
    type=str,
    help="The UUID4 `project-id` under which the entities will be registered",
)
def run(input_dir, project_id):
    """Import data script."""
    with (
        closing(configure_database_session_manager()) as database_session_manager,
        database_session_manager.session() as db,
    ):
        _do_import(db, input_dir=input_dir, project_id=UUID4(project_id))
    _analyze()


@cli.command()
@click.argument("hierarchy_path", type=REQUIRED_PATH)
def hierarchy(hierarchy_path):
    """Load a hierarchy.json."""

    with open(hierarchy_path) as fd:
        hierarchy = json.load(fd)
        if "msg" in hierarchy:
            hierarchy = hierarchy["msg"][0]

    regions = []

    def recurse(i):
        children = []
        item = i | {"children": children}
        for child in i["children"]:
            children.append(child["id"])
            recurse(child)
        regions.append(item)

    recurse(hierarchy)

    with (
        closing(configure_database_session_manager()) as database_session_manager,
        database_session_manager.session() as db,
    ):
        for region in tqdm(regions):
            if orig := db.query(BrainRegion).filter(BrainRegion.id == region["id"]).first():
                continue

            db_br = BrainRegion(
                id=region["id"],
                name=region["name"],
                acronym=region["acronym"],
                children=region["children"],
            )
            db.add(db_br)
            db.commit()
    _analyze()


if __name__ == "__main__":
    cli()
