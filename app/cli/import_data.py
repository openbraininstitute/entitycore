import datetime
import glob
import json
import os
from collections import Counter, defaultdict
from contextlib import closing
from pathlib import Path
from collections import defaultdict
from abc import ABC, abstractmethod

import click
import sqlalchemy as sa
from tqdm import tqdm

from app.cli import curate, utils
from app.cli.utils import AUTHORIZED_PUBLIC
from app.db.model import (
    AnalysisSoftwareSourceCode,
    Annotation,
    Asset,
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
    MTypeClass,
    MTypeClassification,
    Organization,
    Person,
    ReconstructionMorphology,
    Root,
    SingleCellExperimentalTrace,
    SingleNeuronSimulation,
)
from app.db.session import configure_database_session_manager
from app.logger import L
from app.schemas.base import PointLocationBase, ProjectContext

REQUIRED_PATH = click.Path(exists=True, readable=True, dir_okay=False, resolve_path=True)
REQUIRED_PATH_DIR = click.Path(
    exists=True, readable=True, file_okay=False, dir_okay=True, resolve_path=True
)

SQLA_ENGINE_ARGS = {
    # "echo_pool": "debug",
    "executemany_mode": "values_plus_batch",
    "pool_use_lifo": True,
    "pool_size": 1,
}


def ensurelist(x):
    return x if isinstance(x, list) else [x]


def get_or_create_annotation_body(annotation_body, db):
    annotation_body = curate.curate_annotation_body(annotation_body)
    annotation_types = {
        "EType": ETypeAnnotationBody,
        "MType": MTypeClass,
        "DataMaturity": DataMaturityAnnotationBody,
        "DataScope": None,
    }
    annotation_type_list = annotation_body["@type"]
    intersection = [value for value in annotation_type_list if value in annotation_types]

    assert len(intersection) == 1, f"Unknown annotation body type {annotation_body['@type']}"
    annotation_type = annotation_types[intersection[0]]
    # TODO manage datascope
    if annotation_type is None:
        return annotation_type, None

    ab = (
        db.query(annotation_type)
        .filter(annotation_type.pref_label == annotation_body["label"])
        .first()
    )
    if not ab:
        if annotation_type is MTypeClass:
            msg = f"Missing mtype in annotation body {annotation_body}"
            raise ValueError(msg)
        ab = annotation_type(pref_label=annotation_body["label"])
        db.add(ab)
        db.commit()
    return annotation_type, ab.id


def create_annotation(annotation_, entity_id, db):
    annotation_type, annotation_body_id = get_or_create_annotation_body(annotation_["hasBody"], db)

    if not annotation_body_id:
        return None

    if annotation_type is MTypeClass:
        createdBy_id = None
        updatedBy_id = None

        if "contribution" in annotation_:
            # Example contribution, in this case
            # 'contribution': {'@type': 'Contribution',
            #                  'agent': {'@id': 'https://bbp.epfl.ch/nexus/v1/realms/bbp/users/foobar',
            #                            '@type': ['Agent', 'Person'],
            #                            'familyName': 'Bar', 'givenName': 'Foo'}},
            contribution = annotation_["contribution"]
            assert contribution["@type"] == "Contribution"
            legacy_id = contribution["agent"]["@id"]

            agent = utils._find_by_legacy_id(legacy_id, Person, db)
            assert agent

            createdBy_id = agent.id
            updatedBy_id = agent.id

        row = MTypeClassification(
            entity_id=entity_id,
            mtype_class_id=annotation_body_id,
            createdBy_id=createdBy_id,
            updatedBy_id=updatedBy_id,
        )
    else:
        row = Annotation(
            entity_id=entity_id,
            note=annotation_.get("note", None),
            annotation_body_id=annotation_body_id,
        )

    db.add(row)
    db.commit()


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
        except Exception as e:
            print(f"Error creating license: {e!r}")
            print(license)
            raise

    db.commit()


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
        db.flush()
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
    _import_annotation_body(data, MTypeClass, db)


def import_etype_annotation_body(data, db):
    _import_annotation_body(data, ETypeAnnotationBody, db)


class Import(ABC):
    name = "ToName"
    defaults = None

    @staticmethod
    @abstractmethod
    def is_correct_type(data):
        """filter if the `data` is applicable to this `Import`"""

    @staticmethod
    @abstractmethod
    def ingest(db, project_context, data_list):
        """data that is passes `is_correct_type` will be fed to this to ingest into `db`"""


class ImportAgent(Import):
    name = "agents"
    defaults = curate.default_agents()

    @staticmethod
    def is_correct_type(data):
        return {"Person", "Organization"} & set(ensurelist(data.get("@type", [])))

    @staticmethod
    def ingest(db, project_context, data_list):
        for data in tqdm(data_list):
            if "Person" in ensurelist(data["@type"]):
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
            elif "Organization" in ensurelist(data["@type"]):
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


class ImportAnalysisSoftwareSourceCode(Import):
    name = "AnalysisSoftwareSourceCode"

    @staticmethod
    def is_correct_type(data):
        return "AnalysisSoftwareSourceCode" in ensurelist(data["@type"])

    @staticmethod
    def ingest(db, project_context, data_list):
        for data in tqdm(data_list):
            legacy_id = data["@id"]
            rm = utils._find_by_legacy_id(legacy_id, AnalysisSoftwareSourceCode, db)
            if rm:
                continue

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
                authorized_project_id=project_context.project_id,
                authorized_public=AUTHORIZED_PUBLIC,
            )
            db.add(db_code)

        db.commit()


class ImportEModels(Import):
    name = "EModels"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data["@type"])
        return "EModel" in types

    @staticmethod
    def ingest(db, project_context, data_list):
        for data in tqdm(data_list):
            legacy_id = data["@id"]
            db_item = utils._find_by_legacy_id(legacy_id, EModel, db)

            if db_item:
                continue

            _brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            assert _brain_location is None

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
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=strain_id,
                createdBy_id=created_by_id,
                updatedBy_id=updated_by_id,
                creation_date=createdAt,
                update_date=updatedAt,
                authorized_project_id=project_context.project_id,
                authorized_public=AUTHORIZED_PUBLIC,
            )

            db.add(db_item)
            db.commit()
            utils.import_contribution(data, db_item.id, db)

            for annotation in ensurelist(data.get("annotation", [])):
                create_annotation(annotation, db_item.id, db)


class ImportBrainRegionMeshes(Import):
    name = "BrainRegionMeshes"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data["@type"])
        return "BrainParcellationMesh" in types

    @staticmethod
    def ingest(db, project_context, data_list):
        for data in tqdm(data_list):
            legacy_id = data["@id"]
            rm = utils._find_by_legacy_id(legacy_id, Mesh, db)
            if rm:
                continue

            _brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            assert _brain_location is None

            createdAt, updatedAt = utils.get_created_and_updated(data)

            content_url = data.get("distribution").get("contentUrl")

            db_item = Mesh(
                legacy_id=[legacy_id],
                brain_region_id=brain_region_id,
                content_url=content_url,
                creation_date=createdAt,
                update_date=updatedAt,
                authorized_project_id=project_context.project_id,
                authorized_public=AUTHORIZED_PUBLIC,
            )
            db.add(db_item)
        db.commit()


class ImportMorphologies(Import):
    name = "Morphologies"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data["@type"])
        return {"NeuronMorphology", "ReconstructedNeuronMorphology"} & set(types)

    @staticmethod
    def ingest(db, project_context, data_list):
        for data in tqdm(data_list):
            curate.curate_morphology(data)
            legacy_id = data["@id"]
            rm = utils._find_by_legacy_id(legacy_id, ReconstructionMorphology, db)
            if rm:
                continue

            brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            license_id = utils.get_license_mixin(data, db)
            species_id, strain_id = utils.get_species_mixin(data, db)
            createdAt, updatedAt = utils.get_created_and_updated(data)

            db_reconstruction_morphology = ReconstructionMorphology(
                legacy_id=[data.get("@id", None)],
                name=data["name"],
                description=data["description"],
                location=brain_location and PointLocationBase(**brain_location),
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=strain_id,
                license_id=license_id,
                creation_date=createdAt,
                update_date=updatedAt,
                authorized_project_id=project_context.project_id,
                authorized_public=AUTHORIZED_PUBLIC,
            )

            db.add(db_reconstruction_morphology)
            db.commit()
            db.refresh(db_reconstruction_morphology)

            utils.import_contribution(data, db_reconstruction_morphology.id, db)

            for annotation in ensurelist(data.get("annotation", [])):
                create_annotation(annotation, db_reconstruction_morphology.id, db)


class ImportExperimentalNeuronDensities(Import):
    name = "ExperimentalNeuronDensities"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data["@type"])
        return "ExperimentalNeuronDensity" in types

    @staticmethod
    def ingest(db, project_context, data_list):
        _import_experimental_densities(
            db,
            project_context,
            ExperimentalNeuronDensity,
            curate.default_curate,
            data_list,
        )


class ImportExperimentalBoutonDensity(Import):
    name = "ExperimentalBoutonDensity"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data["@type"])
        return "ExperimentalBoutonDensity" in types

    @staticmethod
    def ingest(db, project_context, data_list):
        _import_experimental_densities(
            db,
            project_context,
            ExperimentalBoutonDensity,
            curate.default_curate,
            data_list,
        )


class ImportExperimentalSynapsesPerConnection(Import):
    name = "ExperimentalSynapsesPerConnection"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data["@type"])
        return "ExperimentalSynapsesPerConnection" in types

    @staticmethod
    def ingest(db, project_context, data_list):
        _import_experimental_densities(
            db,
            project_context,
            ExperimentalSynapsesPerConnection,
            curate.default_curate,
            data_list,
        )


class ImportSingleCellExperimentalTrace(Import):
    name = "SingleCellExperimentalTrace"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data["@type"])
        return "SingleCellExperimentalTrace" in types

    @staticmethod
    def ingest(db, project_context, data_list):
        for data in tqdm(data_list):
            legacy_id = data["@id"]
            rm = utils._find_by_legacy_id(legacy_id, SingleCellExperimentalTrace, db)
            if rm:
                continue

            data = curate.curate_trace(data)

            _brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            assert _brain_location is None

            license_id = utils.get_license_mixin(data, db)
            species_id, strain_id = utils.get_species_mixin(data, db)
            createdAt, updatedAt = utils.get_created_and_updated(data)

            db_item = SingleCellExperimentalTrace(
                legacy_id=[data.get("@id", None)],
                name=data["name"],
                description=data["description"],
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=strain_id,
                license_id=license_id,
                creation_date=createdAt,
                update_date=updatedAt,
                authorized_project_id=project_context.project_id,
                authorized_public=AUTHORIZED_PUBLIC,
            )

            db.add(db_item)
            db.commit()
            db.refresh(db_item)

            utils.import_contribution(data, db_item.id, db)

            for annotation in ensurelist(data.get("annotation", [])):
                create_annotation(annotation, db_item.id, db)


class ImportMEModel(Import):
    name = "MEModel"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data["@type"])
        return "MEModel" in types or "https://neuroshapes.org/MEModel" in types

    @staticmethod
    def ingest(db, project_context, data_list):
        for data in tqdm(data_list):
            legacy_id = data["@id"]
            rm = utils._find_by_legacy_id(legacy_id, MEModel, db)
            if rm:
                continue

            _brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            assert _brain_location is None

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
                brain_region_id=brain_region_id,
                createdBy_id=created_by_id,
                updatedBy_id=updated_by_id,
                authorized_project_id=project_context.project_id,
                authorized_public=AUTHORIZED_PUBLIC,
                # species_id=species_id,
                # strain_id=strain_id
                creation_date=createdAt,
                update_date=updatedAt,
            )
            db.add(rm)
        db.commit()
        # create_annotation(data, rm.id, db)


class ImportSingleNeuronSimulation(Import):
    name = "SingleNeuronSimulation"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data["@type"])
        return "SingleNeuronSimulation" in types

    @staticmethod
    def ingest(db, project_context, data_list):
        for data in tqdm(data_list):
            legacy_id = data["@id"]
            rm = utils._find_by_legacy_id(legacy_id, SingleNeuronSimulation, db)
            if rm:
                continue

            _brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
            assert _brain_location is None

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
                authorized_project_id=project_context.project_id,
                authorized_public=AUTHORIZED_PUBLIC,
            )
            db.add(rm)
        db.commit()


class ImportDistribution(Import):
    name = "Distribution"

    @staticmethod
    def is_correct_type(data):
        return "distribution" in data

    @staticmethod
    def ingest(db, project_context, data_list):
        ignored = Counter()
        for data in tqdm(data_list):
            legacy_id = data["@id"]
            root = utils._find_by_legacy_id(legacy_id, Root, db)
            if root:
                utils.import_distribution(data, root.id, root.type, db, project_context)
            else:
                dt = data["@type"]
                types = tuple(sorted(dt)) if isinstance(dt, list) else dt
                ignored[types] += 1

        if ignored:
            L.warning("Ignored assets by type: {}", ignored)


class ImportNeuronMorphologyFeatureAnnotation(Import):
    name = "NeuronMorphologyFeatureAnnotation"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data["@type"])
        return "NeuronMorphologyFeatureAnnotation" in types

    @staticmethod
    def ingest(db, project_context, data_list):
        annotations = defaultdict(list)
        missing_morphology = 0
        duplicate_annotation = 0

        for data in tqdm(data_list):
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
                serie = ensurelist(measurement.get("value", {}).get("series", []))

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
            except Exception as e:
                print(f"Error: {e!r}")
                print(data)
                raise

        db.commit()
        print(
            f"    Annotations related to a morphology that isn't registered: {missing_morphology}\n",
            f"    Duplicate_annotation: {duplicate_annotation}\n",
            f"    Previously registered: {already_registered}\n",
            f"    Total Duplicate: {duplicate_annotation + already_registered}",
        )


def _import_experimental_densities(db, project_context, model_type, curate_function, data_list):
    for data in tqdm(data_list):
        data = curate_function(data)
        legacy_id = data["@id"]
        db_element = utils._find_by_legacy_id(legacy_id, model_type, db)
        if db_element:
            continue

        license_id = utils.get_license_mixin(data, db)
        species_id, strain_id = utils.get_species_mixin(data, db)
        _brain_location, brain_region_id = utils.get_brain_location_mixin(data, db)
        assert _brain_location is None
        createdBy_id, updatedBy_id = utils.get_agent_mixin(data, db)

        createdAt, updatedAt = utils.get_created_and_updated(data)

        db_element = model_type(
            legacy_id=[legacy_id],
            name=data.get("name"),
            description=data.get("description", data.get("name")),
            species_id=species_id,
            strain_id=strain_id,
            license_id=license_id,
            brain_region_id=brain_region_id,
            createdBy_id=createdBy_id,
            updatedBy_id=updatedBy_id,
            creation_date=createdAt,
            update_date=updatedAt,
            authorized_project_id=project_context.project_id,
            authorized_public=AUTHORIZED_PUBLIC,
        )
        db.add(db_element)
        db.commit()
        utils.import_contribution(data, db_element.id, db)


def _do_import(db, input_dir, project_context):
    print("import licenses")
    import_licenses(curate.default_licenses(), db)
    with open(os.path.join(input_dir, "bbp", "licenses", "provEntity.json")) as f:
        data = json.load(f)
        import_licenses(data, db)

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

    importers = [
        ImportAgent,
        ImportAnalysisSoftwareSourceCode,
        ImportEModels,
        ImportBrainRegionMeshes,
        ImportMorphologies,
        ImportExperimentalNeuronDensities,
        ImportExperimentalBoutonDensity,
        ImportExperimentalSynapsesPerConnection,
        ImportSingleCellExperimentalTrace,
        ImportMEModel,
        ImportSingleNeuronSimulation,
        ImportDistribution,
        ImportNeuronMorphologyFeatureAnnotation,
    ]

    for importer in importers:
        if importer.defaults:
            print(f"importing default {importer.name}")
            importer.ingest(db, project_context, importer.defaults)

    import_data = defaultdict(list)

    print("Loading files")
    all_files = sorted(glob.glob(os.path.join(input_dir, "*", "*", "*.json")))
    for file_path in tqdm(all_files):
        with open(file_path) as f:
            data = json.load(f)
            for importer in importers:
                import_data[importer].extend(d for d in data if importer.is_correct_type(d))

    for importer, data in import_data.items():
        print(f"ingesting {importer.name}")
        importer.ingest(db, project_context, data)


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
    "--virtual-lab-id",
    type=str,
    help="The UUID4 `virtual-lab-id` under which the entities will be registered",
)
@click.option(
    "--project-id",
    type=str,
    help="The UUID4 `project-id` under which the entities will be registered",
)
def run(input_dir, virtual_lab_id, project_id):
    """Import data script."""
    project_context = ProjectContext(virtual_lab_id=virtual_lab_id, project_id=project_id)
    with (
        closing(configure_database_session_manager(**SQLA_ENGINE_ARGS)) as database_session_manager,
        database_session_manager.session() as db,
    ):
        _do_import(db, input_dir=input_dir, project_context=project_context)
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
        closing(configure_database_session_manager(**SQLA_ENGINE_ARGS)) as database_session_manager,
        database_session_manager.session() as db,
    ):
        ids = set(db.execute(sa.select(BrainRegion.id)).scalars())
        for region in tqdm(regions):
            if region["id"] in ids:
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


@cli.command()
@click.argument("digest_path", type=REQUIRED_PATH)
def organize_files(digest_path):
    """Copy files to the expected location.

    The digest file should contain lines like:

        6fc954f05e23b1b5aefa9043b0628872154f356f09e48d112b8554325199b8c8 download/...

    generated with:

        find download -type f | xargs sha256 -r

    It's acceptable that different files have the same digest.
    """
    with Path(digest_path).open("r", encoding="utf-8") as f:
        src_paths = dict(line.strip().split(" ", maxsplit=1) for line in f)
    ignored = src_paths.copy()  # for debugging
    with (
        closing(configure_database_session_manager()) as database_session_manager,
        database_session_manager.session() as db,
    ):
        query = sa.select(Asset.full_path, Asset.sha256_digest)
        rows = db.execute(query).all()
        for row in tqdm(rows):
            dst = Path(row.full_path)
            digest = row.sha256_digest.hex()
            ignored.pop(digest, None)
            if not dst.exists():
                src = Path(src_paths[digest]).resolve()
                assert src.exists()
                dst = Path(row.full_path)
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.symlink_to(src)
    if ignored:
        L.info("Ignored files: {}", len(ignored))


if __name__ == "__main__":
    cli()
