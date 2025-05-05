import datetime
import glob
import json
import os
import random
import uuid
from functools import partial
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from contextlib import closing
from pathlib import Path
from typing import Any
from app.cli.utils import ensurelist
from sqlalchemy.orm import Session
from app.schemas.base import ProjectContext
from app.db.types import EntityType

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
    BrainRegionHierarchyName,
    DataMaturityAnnotationBody,
    ElectricalCellRecording,
    EModel,
    Entity,
    ETypeClass,
    ETypeClassification,
    ExperimentalBoutonDensity,
    ExperimentalNeuronDensity,
    ExperimentalSynapsesPerConnection,
    License,
    MEModel,
    Measurement,
    Mesh,
    MorphologyFeatureAnnotation,
    MorphologyMeasurement,
    MorphologyMeasurementSerieElement,
    MTypeClass,
    MTypeClassification,
    Organization,
    Person,
    ReconstructionMorphology,
    SingleNeuronSimulation,
    Subject,
)
from app.db.session import configure_database_session_manager
from app.logger import L
from app.schemas.base import ProjectContext
from app.db.types import (
    ElectricalRecordingType,
    ElectricalRecordingOrigin,
    MeasurementStatistic,
    MeasurementUnit,
    PointLocationBase,
)

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


def get_or_create_annotation_body(annotation_body, db):
    annotation_body = curate.curate_annotation_body(annotation_body)
    annotation_types = {
        "EType": ETypeClass,
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

        if annotation_type is ETypeClass:
            msg = f"Missing etype in annotation body {annotation_body}"
            raise ValueError(msg)

        ab = annotation_type(pref_label=annotation_body["label"])
        db.add(ab)
        db.commit()
    return annotation_type, ab.id


def create_annotation(annotation_, entity_id, db):
    annotation_type, annotation_body_id = get_or_create_annotation_body(annotation_["hasBody"], db)

    if not annotation_body_id:
        return None

    def get_agent_id_from_contribution(annotation_) -> int | None:
        agent = None

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

        return agent and agent.id

    agent_id = None

    if annotation_type in [MTypeClass, ETypeClass]:
        agent_id = get_agent_id_from_contribution(annotation_)

    assert agent_id is None or isinstance(agent_id, uuid.UUID)

    if annotation_type is MTypeClass:
        row = MTypeClassification(
            entity_id=entity_id,
            mtype_class_id=annotation_body_id,
            createdBy_id=agent_id,
            updatedBy_id=agent_id,
        )

    elif annotation_type is ETypeClass:
        row = ETypeClassification(
            entity_id=entity_id,
            etype_class_id=annotation_body_id,
            createdBy_id=agent_id,
            updatedBy_id=agent_id,
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
                legacy_self=[license["_self"]],
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
        if db_type_ == ETypeClass:
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
            legacy_self=[class_elem["_self"]],
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
            "_self": "",
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
            "_self": "",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        }
    )
    _import_annotation_body(data, MTypeClass, db)


def import_etype_annotation_body(data, db):
    _import_annotation_body(data, ETypeClass, db)


class Import(ABC):
    name = "ToName"
    defaults = None

    @staticmethod
    @abstractmethod
    def is_correct_type(data) -> bool:
        """filter if the `data` is applicable to this `Import`"""

    @staticmethod
    @abstractmethod
    def ingest(db, project_context, data_list, all_data_by_id: dict[str, Any], hierarchy_name: str):
        """data that is passes `is_correct_type` will be fed to this to ingest into `db`"""


class ImportAgent(Import):
    name = "agents"
    defaults = curate.default_agents()

    @staticmethod
    def is_correct_type(data):
        return bool({"Person", "Organization"} & set(ensurelist(data.get("@type", []))))

    @staticmethod
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name: str):
        for data in tqdm(data_list):
            if "Person" in ensurelist(data["@type"]):
                legacy_id = data["@id"]
                legacy_self = data["_self"]
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
                            db_agent.legacy_id = [*db_agent.legacy_id, legacy_id]
                            db_agent.legacy_self = [*db_agent.legacy_self, legacy_self]
                            db.commit()
                        else:
                            createdAt, updatedAt = utils.get_created_and_updated(data)
                            db_agent = Person(
                                legacy_id=[legacy_id],
                                legacy_self=[legacy_self],
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
                legacy_self = data["_self"]
                db_agent = utils._find_by_legacy_id(legacy_id, Organization, db)
                if not db_agent:
                    try:
                        name = data["name"]
                        db_agent = (
                            db.query(Organization).filter(Organization.pref_label == name).first()
                        )
                        if db_agent:
                            db_agent.legacy_id = [*db_agent.legacy_id, legacy_id]
                            db_agent.legacy_self = [*db_agent.legacy_self, legacy_self]
                            db.commit()
                        else:
                            createdAt, updatedAt = utils.get_created_and_updated(data)
                            db_agent = Organization(
                                legacy_id=[legacy_id],
                                legacy_self=[legacy_self],
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
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name: str):
        for data in tqdm(data_list):
            legacy_id = data["@id"]
            legacy_self = data["_self"]
            rm = utils._find_by_legacy_id(legacy_id, AnalysisSoftwareSourceCode, db)
            if rm:
                continue

            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)
            createdAt, updatedAt = utils.get_created_and_updated(data)

            db_code = AnalysisSoftwareSourceCode(
                legacy_id=[legacy_id],
                legacy_self=[legacy_self],
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
    def ingest(
        db,
        project_context,
        data_list: list[dict],
        all_data_by_id: dict[str, dict],
        hierarchy_name: str,
    ):
        for data in tqdm(data_list):
            legacy_id = data["@id"]
            legacy_self = data["_self"]
            db_item = utils._find_by_legacy_id(legacy_id, EModel, db)

            if db_item:
                continue

            brain_region_id = utils.get_brain_region(data, hierarchy_name, db)

            species_id, strain_id = utils.get_species_mixin(data, db)
            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)
            createdAt, updatedAt = utils.get_created_and_updated(data)

            workflow_id = (
                data.get("generation", {}).get("activity", {}).get("followedWorkflow").get("@id")
            )

            workflow = all_data_by_id.get(workflow_id)

            configuration_id = utils.find_id_in_entity(workflow, "EModelConfiguration", "hasPart")

            configuration = configuration_id and all_data_by_id.get(configuration_id)

            assert configuration

            exemplar_morphology_id = utils.find_id_in_entity(
                configuration, "NeuronMorphology", "uses"
            )

            morphology = utils._find_by_legacy_id(
                exemplar_morphology_id, ReconstructionMorphology, db
            )

            assert morphology

            emodel_script_id = utils.find_id_in_entity(workflow, "EModelScript", "generates")
            emodel_script = emodel_script_id and all_data_by_id.get(emodel_script_id)

            assert emodel_script

            db_emodel = EModel(
                legacy_id=[legacy_id],
                legacy_self=[legacy_self],
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
                exemplar_morphology_id=morphology.id,
            )

            db.add(db_emodel)

            db.flush()

            utils.import_ion_channel_models(
                configuration, db_emodel.id, all_data_by_id, project_context, hierarchy_name, db
            )

            utils.import_contribution(data, db_emodel.id, db)

            # Import hoc file
            utils.import_distribution(
                emodel_script, db_emodel.id, EntityType.emodel, db, project_context
            )

            for annotation in ensurelist(data.get("annotation", [])):
                create_annotation(annotation, db_emodel.id, db)

        db.commit()


class ImportBrainRegionMeshes(Import):
    name = "BrainRegionMeshes"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data["@type"])
        return "BrainParcellationMesh" in types

    @staticmethod
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name: str):
        for data in tqdm(data_list):
            legacy_id = data["@id"]
            legacy_self = data["_self"]
            rm = utils._find_by_legacy_id(legacy_id, Mesh, db)
            if rm:
                continue

            try:
                brain_region_id = utils.get_brain_region(data, hierarchy_name, db)
            except RuntimeError:
                L.exception("Cannot import mesh")
                continue

            createdAt, updatedAt = utils.get_created_and_updated(data)

            db_item = Mesh(
                name=data["name"],
                description=data["description"],
                legacy_id=[legacy_id],
                legacy_self=[legacy_self],
                brain_region_id=brain_region_id,
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
        return bool({"NeuronMorphology", "ReconstructedNeuronMorphology"} & set(types))

    @staticmethod
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name: str):
        for data in tqdm(data_list):
            curate.curate_morphology(data)
            legacy_id = data["@id"]
            legacy_self = data["_self"]
            rm = utils._find_by_legacy_id(legacy_id, ReconstructionMorphology, db)
            if rm:
                continue

            brain_region_id = utils.get_brain_region(data, hierarchy_name, db)
            brain_location = utils.get_brain_location(data, db)
            license_id = utils.get_license_mixin(data, db)
            species_id, strain_id = utils.get_species_mixin(data, db)
            createdAt, updatedAt = utils.get_created_and_updated(data)

            db_reconstruction_morphology = ReconstructionMorphology(
                legacy_id=[legacy_id],
                legacy_self=[legacy_self],
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
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name: str):
        _import_experimental_densities(
            db,
            project_context,
            ExperimentalNeuronDensity,
            curate.default_curate,
            hierarchy_name=hierarchy_name,
            data_list=data_list,
        )


class ImportExperimentalBoutonDensity(Import):
    name = "ExperimentalBoutonDensity"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data["@type"])
        return "ExperimentalBoutonDensity" in types

    @staticmethod
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name: str):
        _import_experimental_densities(
            db,
            project_context,
            ExperimentalBoutonDensity,
            curate.default_curate,
            hierarchy_name=hierarchy_name,
            data_list=data_list,
        )


class ImportExperimentalSynapsesPerConnection(Import):
    name = "ExperimentalSynapsesPerConnection"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data["@type"])
        return "ExperimentalSynapsesPerConnection" in types

    @staticmethod
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name: str):
        _import_experimental_densities(
            db,
            project_context,
            ExperimentalSynapsesPerConnection,
            curate.default_curate,
            hierarchy_name=hierarchy_name,
            data_list=data_list,
        )


class ImportElectricalCellRecording(Import):
    name = "SingleCellExperimentalTrace"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data["@type"])
        return (
            "SingleCellExperimentalTrace" in types
            or "Trace" in types
            or "ExperimentalTrace" in types
        )

    @staticmethod
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name: str):
        for data in tqdm(data_list):
            legacy_id = data["@id"]
            legacy_self = data["_self"]
            rm = utils._find_by_legacy_id(legacy_id, ElectricalCellRecording, db)
            if rm:
                continue

            data = curate.curate_trace(data)

            brain_region_id = utils.get_brain_region(data, hierarchy_name, db)

            license_id = utils.get_license_mixin(data, db)
            # species_id, strain_id = utils.get_species_mixin(data, db)

            subject_id = utils.get_or_create_subject(data, project_context, db)
            createdAt, updatedAt = utils.get_created_and_updated(data)

            age = data.get("subject", {}).get("age", {}).get("value", None)
            comment = data.get("note", None)

            if "ExperimentalTrace" in data["@type"]:
                recording_origin = ElectricalRecordingOrigin.in_vitro
            elif "SimulationTrace" in data["@type"]:
                recording_origin = ElectricalRecordingOrigin.in_silico
            else:
                recording_origin = ElectricalRecordingOrigin.unknown
                msg = f"Trace type {data['@type']} has unknown origin."
                L.warning(msg)

            db_item = ElectricalCellRecording(
                legacy_id=[legacy_id],
                legacy_self=[legacy_self],
                name=data["name"],
                description=data["description"],
                comment=comment,
                brain_region_id=brain_region_id,
                subject_id=subject_id,
                license_id=license_id,
                recording_type=ElectricalRecordingType.intracellular,
                recording_location=[],
                recording_origin=recording_origin,
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

            for stimulus in ensurelist(data.get("stimulus", [])):
                stimulus_type = stimulus["stimulusType"]
                if "@id" in stimulus_type and stimulus_type["@id"] in all_data_by_id:
                    stimulus_type = all_data_by_id[stimulus_type["@id"]]

                # create a stimulus for each stimulus in the data
                utils.create_stimulus(stimulus_type, db_item.id, project_context, db)


class ImportMEModel(Import):
    name = "MEModel"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data["@type"])
        return "MEModel" in types or "https://neuroshapes.org/MEModel" in types

    @staticmethod
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name: str):
        for data in tqdm(data_list):
            legacy_id = data["@id"]
            legacy_self = data["_self"]
            rm = utils._find_by_legacy_id(legacy_id, MEModel, db)
            if rm:
                continue

            brain_region_id = utils.get_brain_region(data, hierarchy_name, db)

            morphology_id = utils.find_part_id(data, "NeuronMorphology")
            morphology = utils._find_by_legacy_id(morphology_id, ReconstructionMorphology, db)

            emodel_id = utils.find_part_id(data, "EModel")
            emodel = utils._find_by_legacy_id(emodel_id, EModel, db)

            assert morphology
            assert emodel

            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)
            createdAt, updatedAt = utils.get_created_and_updated(data)
            db_item = MEModel(
                legacy_id=[legacy_id],
                legacy_self=[legacy_self],
                name=data.get("name", None),
                description=data.get("description", None),
                validation_status=data.get("status", None),
                brain_region_id=brain_region_id,
                createdBy_id=created_by_id,
                updatedBy_id=updated_by_id,
                authorized_project_id=project_context.project_id,
                authorized_public=AUTHORIZED_PUBLIC,
                species_id=morphology.species_id,
                morphology_id=morphology.id,
                emodel_id=emodel.id,
                strain_id=morphology.strain_id,
                creation_date=createdAt,
                update_date=updatedAt,
            )
            db.add(db_item)
            db.flush()

            utils.import_contribution(data, db_item.id, db)

            for annotation in ensurelist(data.get("annotation", [])):
                create_annotation(annotation, db_item.id, db)

        db.commit()


class ImportSingleNeuronSimulation(Import):
    name = "SingleNeuronSimulation"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data["@type"])
        return "SingleNeuronSimulation" in types

    @staticmethod
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name: str):
        for data in tqdm(data_list):
            legacy_id = data["@id"]
            legacy_self = data["_self"]
            rm = utils._find_by_legacy_id(legacy_id, SingleNeuronSimulation, db)
            if rm:
                continue

            brain_region_id = utils.get_brain_region(data, hierarchy_name, db)

            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)
            me_model_lid = data.get("used", {}).get("@id", None)
            me_model = utils._find_by_legacy_id(me_model_lid, MEModel, db)
            rm = SingleNeuronSimulation(
                legacy_id=[legacy_id],
                legacy_self=[legacy_self],
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
        return "distribution" in data and not utils.is_type(data, "SubCellularModelScript")

    @staticmethod
    def ingest(
        db: Session,
        project_context: ProjectContext,
        data_list: list[dict],
        all_data_by_id: dict,
        hierarchy_name: str,
    ):
        ignored: dict[tuple[dict], int] = Counter()
        for data in tqdm(data_list):
            legacy_id = data["@id"]
            root = utils._find_by_legacy_id(legacy_id, Entity, db)
            if root:
                utils.import_distribution(data, root.id, root.type, db, project_context)
            else:
                dt = data["@type"]
                types = tuple(sorted(dt)) if isinstance(dt, list) else (dt,)
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
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name: str):
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


def _import_experimental_densities(
    db, project_context, model_type, curate_function, hierarchy_name, data_list
):
    for data in tqdm(data_list):
        data = curate_function(data)
        legacy_id = data["@id"]
        legacy_self = data["_self"]
        db_element = utils._find_by_legacy_id(legacy_id, model_type, db)
        if db_element:
            continue

        license_id = utils.get_license_mixin(data, db)

        subject_id = utils.get_or_create_subject(data, project_context, db)

        brain_region_id = utils.get_brain_region(data, hierarchy_name, db)
        createdBy_id, updatedBy_id = utils.get_agent_mixin(data, db)

        createdAt, updatedAt = utils.get_created_and_updated(data)

        kwargs = {
            "legacy_id": [legacy_id],
            "legacy_self": [legacy_self],
            "name": data.get("name"),
            "description": data.get("description", ""),
            "subject_id": subject_id,
            "license_id": license_id,
            "brain_region_id": brain_region_id,
            "createdBy_id": createdBy_id,
            "updatedBy_id": updatedBy_id,
            "creation_date": createdAt,
            "update_date": updatedAt,
            "authorized_project_id": project_context.project_id,
            "authorized_public": AUTHORIZED_PUBLIC,
        }

        if model_type is ExperimentalSynapsesPerConnection:
            try:
                pathway_id = utils.get_or_create_synaptic_pathway(
                    data["synapticPathway"], project_context, hierarchy_name, db
                )
                kwargs["synaptic_pathway_id"] = pathway_id
            except Exception as e:
                msg = f"Failed to create synaptic pathway: {data['synapticPathway']}.\nReason: {e}"
                L.warning(msg)
                continue

        db_item = model_type(**kwargs)
        db.add(db_item)
        db.commit()
        utils.import_contribution(data, db_item.id, db)

        for annotation in ensurelist(data.get("annotation", [])):
            create_annotation(annotation, db_item.id, db)

        for measurement in ensurelist(data.get("series", [])):
            create_measurement(measurement, db_item.id, db)


def create_measurement(data, entity_id, db):
    match data["statistic"]:
        case "N":
            statistic = MeasurementStatistic.sample_size
        case "mean":
            statistic = MeasurementStatistic.mean
        case "standard deviation":
            statistic = MeasurementStatistic.standard_deviation
        case "standard error of the mean":
            statistic = MeasurementStatistic.standard_error
        case "data point":
            statistic = MeasurementStatistic.data_point
        case _:
            statistic = None
            msg = f"Statistic not captured: {data}"
            L.warning(msg)

    match data["unitCode"]:
        case "dimensionless":
            unit = MeasurementUnit.dimensionless
        case "1/μm":
            unit = MeasurementUnit.linear_density__1_um
        case "neurons/mm³":
            unit = MeasurementUnit.volume_density__1_mm3
        case _:
            unit = None
            msg = f"Unit code not captured: {data}"
            L.warning(msg)

    if unit and statistic:
        db_item = Measurement(
            name=statistic,
            unit=unit,
            value=float(data["value"]),
            entity_id=entity_id,
        )
        db.add(db_item)
        db.commit()
    else:
        msg = f"Measurement {data} was skipped."
        L.warning(msg)


def _do_import(db, input_dir, project_context, hierarchy_name):
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
        # ImportBrainRegionMeshes,
        ImportMorphologies,
        ImportEModels,
        ImportExperimentalNeuronDensities,
        ImportExperimentalBoutonDensity,
        ImportExperimentalSynapsesPerConnection,
        ImportMEModel,
        ImportElectricalCellRecording,
        ImportSingleNeuronSimulation,
        ImportDistribution,
        ImportNeuronMorphologyFeatureAnnotation,
    ]

    for importer in importers:
        if importer.defaults:
            print(f"importing default {importer.name}")
            importer.ingest(
                db,
                project_context,
                importer.defaults,
                all_data_by_id=None,
                hierarchy_name=hierarchy_name,
            )

    import_data = defaultdict(list)

    all_files = sorted(glob.glob(os.path.join(input_dir, "*", "*", "*.json")))

    all_data_by_id = {}

    for file_path in tqdm(all_files):
        with open(file_path) as f:
            data = json.load(f)

            for d in data:
                # d["_filename"] = file_path
                id = d["@id"]

                all_data_by_id[id] = d

    for importer in importers:
        import_data[importer].extend(
            d for d in all_data_by_id.values() if importer.is_correct_type(d)
        )

    for importer, data in import_data.items():
        print(f"ingesting {importer.name}")
        importer.ingest(
            db, project_context, data, all_data_by_id=all_data_by_id, hierarchy_name=hierarchy_name
        )


def _analyze() -> None:
    with (
        closing(configure_database_session_manager()) as database_session_manager,
        database_session_manager.session() as db,
    ):
        # running in a transaction although it's not needed
        db.execute(sa.text("ANALYZE"))


@click.group()
@click.option(
    "--seed",
    type=int,
    help="RNG seed to generate UUIDv4, or -1 to not init the seed",
    default=-1,
    show_default=True,
)
def cli(seed):
    """Main CLI group."""
    if seed >= 0:
        click.secho(f"Setting {seed=}")
        random.seed(seed)
        uuid.uuid4 = lambda: uuid.UUID(int=random.getrandbits(128), version=4)


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
@click.option(
    "--hierarchy-name",
    type=str,
    help="Name of the brain atlas to register brain_regions",
)
def run(input_dir, virtual_lab_id, project_id, hierarchy_name):
    """Import data script."""
    project_context = ProjectContext(virtual_lab_id=virtual_lab_id, project_id=project_id)
    with (
        closing(configure_database_session_manager(**SQLA_ENGINE_ARGS)) as database_session_manager,
        database_session_manager.session() as db,
    ):
        _do_import(
            db, input_dir=input_dir, project_context=project_context, hierarchy_name=hierarchy_name
        )
    _analyze()


@cli.command()
@click.argument("hierarchy_name", type=str)
@click.argument("hierarchy_path", type=REQUIRED_PATH)
def hierarchy(hierarchy_name, hierarchy_path):
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
        hier = (
            db.query(BrainRegionHierarchyName)
            .filter(BrainRegionHierarchyName.name == hierarchy_name)
            .first()
        )

        if not hier:
            hier = BrainRegionHierarchyName(name=hierarchy_name)
            db.add(hier)
            db.flush()

        ids = {
            v.hierarchy_id: v.id
            for v in db.execute(
                sa.select(BrainRegion.id, BrainRegion.hierarchy_id).where(
                    BrainRegion.hierarchy_name_id == hier.id
                )
            ).all()
        }
        ids[None] = BrainRegion.ROOT_PARENT_UUID

        for region in tqdm(reversed(regions), total=len(regions)):
            if region["id"] in ids:
                continue

            db_br = BrainRegion(
                hierarchy_id=region["id"],
                name=region["name"],
                acronym=region["acronym"],
                parent_structure_id=ids[region["parent_structure_id"]],
                color_hex_triplet=region["color_hex_triplet"],
                hierarchy_name_id=hier.id,
            )
            db.add(db_br)
            db.flush()
            ids[region["id"]] = db_br.id

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
                assert src.exists(), f"src path doens't exist: {src}"
                dst = Path(row.full_path)
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.symlink_to(src)
    if ignored:
        L.info("Ignored files: {}", len(ignored))


if __name__ == "__main__":
    cli()
