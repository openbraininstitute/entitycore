import datetime
import glob
import json
import os
import random
import uuid
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from contextlib import closing
from pathlib import Path
from typing import Any

import click
import sqlalchemy as sa
from sqlalchemy.orm import Session
from tqdm import tqdm

from app.logger import L
from app.cli import curate, utils
from app.cli.brain_region_data import BRAIN_ATLAS_REGION_VOLUMES
from app.cli.curation import cell_composition, electrical_cell_recording
from app.cli.types import ContentType
from app.cli.utils import (
    AUTHORIZED_PUBLIC,
    build_measurement_item,
    build_measurement_kind,
    ensurelist,
    merge_measurements_annotations,
)
from app.db.model import (
    AnalysisSoftwareSourceCode,
    Annotation,
    Asset,
    BrainAtlas,
    BrainAtlasRegion,
    BrainRegion,
    BrainRegionHierarchy,
    CellComposition,
    DataMaturityAnnotationBody,
    Derivation,
    ElectricalCellRecording,
    EModel,
    Entity,
    ETypeClass,
    ETypeClassification,
    ExperimentalBoutonDensity,
    ExperimentalNeuronDensity,
    ExperimentalSynapsesPerConnection,
    License,
    Measurement,
    MeasurementAnnotation,
    MEModel,
    MEModelCalibrationResult,
    METypeDensity,
    MTypeClass,
    MTypeClassification,
    Organization,
    Person,
    ReconstructionMorphology,
    SingleNeuronSimulation,
    Species,
)
from app.db.session import configure_database_session_manager
from app.db.types import (
    ElectricalRecordingOrigin,
    ElectricalRecordingType,
    EntityType,
    MeasurementStatistic,
    MeasurementUnit,
    PointLocationBase,
)
from app.schemas.base import ProjectContext

BRAIN_ATLAS_NAME = "BlueBrain Atlas"

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

# atlas/composition used by the frontend
BRAIN_ATLAS_ID = "https://bbp.epfl.ch/neurosciencegraph/data/4906ab85-694f-469d-962f-c0174e901885"
CELL_COMPOSITION_ID = "https://bbp.epfl.ch/neurosciencegraph/data/cellcompositions/54818e46-cf8c-4bd6-9b68-34dffbc8a68c"

l_distributions = []


def get_or_create_annotation_body(annotation_body, db, created_by_id, updated_by_id):
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

    if annotation_type is MTypeClass:
        annotation_body = curate.curate_annotation_body(annotation_body)
        if "@id" in annotation_body and annotation_body["@id"] == "nsg:Neuron":
            # Too generic type, nothing to do
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

        ab = annotation_type(
            pref_label=annotation_body["label"],
            created_by_id=created_by_id,
            updated_by_id=updated_by_id,
        )
        db.add(ab)
        db.commit()
    return annotation_type, ab.id


def create_annotation(annotation_, entity_id, db, created_by_id, updated_by_id):
    annotation_type, annotation_body_id = get_or_create_annotation_body(
        annotation_["hasBody"], db, created_by_id, updated_by_id
    )
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
            created_by_id=created_by_id,
            updated_by_id=updated_by_id,
        )

    elif annotation_type is ETypeClass:
        row = ETypeClassification(
            entity_id=entity_id,
            etype_class_id=annotation_body_id,
            created_by_id=created_by_id,
            updated_by_id=updated_by_id,
        )

    else:
        row = Annotation(
            entity_id=entity_id,
            note=annotation_.get("note", None),
            annotation_body_id=annotation_body_id,
            created_by_id=created_by_id,
            updated_by_id=updated_by_id,
        )

    db.add(row)
    db.commit()


def _import_annotation_body(data, db_type_, db):
    for class_elem in tqdm(data):
        if db_type_ == MTypeClass:
            class_elem = curate.curate_mtype(class_elem)

        if db_type_ == ETypeClass:
            class_elem = curate.curate_etype(class_elem)

        db_elem = db.query(db_type_).filter(db_type_.pref_label == class_elem["label"]).first()

        if db_elem:
            assert db_elem.definition == class_elem.get("definition", "")
            assert db_elem.alt_label == class_elem.get("prefLabel", "")

            continue

        createdAt, updatedAt = utils.get_created_and_updated(class_elem)
        created_by_id, updated_by_id = utils.get_agent_mixin(class_elem, db)

        db_elem = db_type_(
            pref_label=class_elem["label"],
            definition=class_elem.get("definition", ""),
            alt_label=class_elem.get("prefLabel", ""),
            legacy_id=[class_elem["@id"]],
            legacy_self=[class_elem["_self"]],
            creation_date=createdAt,
            update_date=updatedAt,
            created_by_id=created_by_id,
            updated_by_id=updated_by_id,
        )

        db.add(db_elem)
        db.flush()
    db.commit()


def import_mtype_annotation_body(data, db):
    # Check if the annotation body already exists in the database
    data.extend(
        [
            {
                "label": "Inhibitory neuron",
                "definition": "Inhibitory neuron",
                "prefLabel": "Inhibitory neuron",
                "@id": "https://bbp.epfl.ch/neurosciencegraph/data/annotation/mtype/Inhibitoryneuron",
                "_self": "",
                "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
                "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            },
            {
                "label": "Excitatory neuron",
                "definition": "Excitatory neuron",
                "prefLabel": "Excitatory neuron",
                "@id": "https://bbp.epfl.ch/neurosciencegraph/data/annotation/mtype/Excitatoryneuron",
                "_self": "",
                "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
                "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            },
            {
                "label": "PV+",
                "definition": "Parvalbumin (PV)-Positive Cell",
                "prefLabel": "PV+",
                "@id": "https://bbp.epfl.ch/ontologies/core/celltypes/PV_plus",
                "_self": "",
                "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
                "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            },
            {
                "label": "VIP+",
                "definition": "Vasoactive Intestinal Peptide (VIP)-Positive cell",
                "prefLabel": "VIP+",
                "@id": "https://bbp.epfl.ch/ontologies/core/celltypes/VIP_plus",
                "_self": "",
                "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
                "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            },
            {
                "label": "SST+",
                "definition": "Somatostatin (SST)-Positive cell",
                "@id": "https://bbp.epfl.ch/ontologies/core/celltypes/SST_plus",
                "_self": "",
                "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
                "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            },
            {
                "label": "Gad67+",
                "definition": "Glutamate decarboxylase 67 (Gad67)-Positive cell",
                "@id": "https://bbp.epfl.ch/ontologies/core/celltypes/Gad67_plus",
                "_self": "",
                "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
                "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            },
            {
                "label": "L2_PC",
                "definition": "Layer 2 pyramidal cell.",
                "@id": "https://bbp.epfl.ch/ontologies/core/celltypes/L2_PC",
                "_self": "",
                "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
                "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            },
            {
                "label": "L3_PC",
                "definition": "Layer 3 pyramidal cell.",
                "@id": "https://bbp.epfl.ch/ontologies/core/celltypes/L3_PC",
                "_self": "",
                "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
                "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            },
            {
                "label": "L4_PC",
                "definition": "Layer 4 pyramidal cell.",
                "@id": "https://bbp.epfl.ch/ontologies/core/celltypes/L4_PC",
                "_self": "",
                "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
                "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            },
            {
                "label": "L5_PC",
                "definition": "Layer 5 pyramidal cell.",
                "@id": "https://bbp.epfl.ch/ontologies/core/celltypes/L5_PC",
                "_self": "",
                "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
                "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            },
            {
                "label": "L6_PC",
                "definition": "Layer 6 pyramidal cell.",
                "@id": "https://bbp.epfl.ch/ontologies/core/celltypes/L6_PC",
                "_self": "",
                "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
                "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            },
            {
                "label": "L56_PC",
                "definition": "Layer 5/6 pyramidal cell.",
                "@id": "https://bbp.epfl.ch/ontologies/core/celltypes/L56_PC",
                "_self": "",
                "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
                "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            },
        ]
    )
    _import_annotation_body(data, MTypeClass, db)


def import_etype_annotation_body(data, db):
    data.extend(
        [
            {
                "label": "bAC_IN",
                "definition": "single-burst-accommodating thalamocortical interneuron e-type",
                "@id": "bmo:bAC_IN",
                "_self": "",
                "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
                "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            }
        ]
    )
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
            if "Person" in ensurelist(data.get("@type", [])):
                legacy_id = data["@id"]
                legacy_self = data["_self"]
                db_agent = utils._find_by_legacy_id(legacy_id, Person, db)
                if not db_agent:
                    try:
                        data, ignore = curate.curate_person(data)
                        if ignore:
                            L.warning(f"Ignoring Person {legacy_id} {legacy_self}")
                            continue
                        given_name = data["givenName"]
                        family_name = data["familyName"]
                        label = f"{given_name} {family_name}"
                        db_agent = (
                            db.query(Person)
                            .filter(
                                Person.given_name == given_name,
                                Person.family_name == family_name,
                            )
                            .first()
                        )
                        if db_agent:
                            db_agent.legacy_id = [*db_agent.legacy_id, legacy_id]
                            db_agent.legacy_self = [*db_agent.legacy_self, legacy_self]
                            db.commit()
                        else:
                            createdAt, updatedAt = utils.get_created_and_updated(data)
                            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)
                            db_agent = Person(
                                legacy_id=[legacy_id],
                                legacy_self=[legacy_self],
                                given_name=data["givenName"],
                                family_name=data["familyName"],
                                pref_label=label,
                                creation_date=createdAt,
                                update_date=updatedAt,
                                created_by_id=created_by_id,
                                updated_by_id=updated_by_id,
                            )
                            db.add(db_agent)
                            db.commit()
                    except Exception as e:
                        print("Error importing person: ", data)
                        print(f"{e!r}")
                        raise
            elif "Organization" in ensurelist(data.get("@type", [])):
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
                            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)
                            db_agent = Organization(
                                legacy_id=[legacy_id],
                                legacy_self=[legacy_self],
                                pref_label=data.get("name"),
                                alternative_name=data.get("alternativeName", ""),
                                creation_date=createdAt,
                                update_date=updatedAt,
                                created_by_id=created_by_id,
                                updated_by_id=updated_by_id,
                            )
                            db.add(db_agent)
                            db.commit()
                    except Exception as e:
                        print("Error importing organization: ", data)
                        print(f"{e!r}")


class ImportSpecies(Import):
    name = "Species"
    defaults = curate.default_species()

    @staticmethod
    def is_correct_type(data):
        return utils.is_type(data, "Species")

    @staticmethod
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name):
        for data in tqdm(data_list):
            createdAt, updatedAt = utils.get_created_and_updated(data)

            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)

            db_species = Species(
                name=data["label"],
                taxonomy_id=data["@id"],
                created_by_id=created_by_id,
                updated_by_id=updated_by_id,
                creation_date=createdAt,
                update_date=updatedAt,
            )

            db.add(db_species)

        db.commit()


class ImportLicense(Import):
    name = "Licenses"
    defaults = curate.default_licenses()

    @staticmethod
    def is_correct_type(data):
        return utils.is_type(data, "License")

    @staticmethod
    def ingest(
        db,
        project_context,
        data_list: list[dict],
        all_data_by_id: dict[str, dict],
        hierarchy_name: str,
    ):
        for data in tqdm(data_list):
            curate.curate_license(data)
            if utils._find_by_legacy_id(data["@id"], License, db):
                continue

            createdAt, updatedAt = utils.get_created_and_updated(data)

            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)

            label = data["label"] if "label" in data else data["name"]

            db_license = License(
                name=data["@id"],
                label=label,
                description=data["description"],
                legacy_id=[data["@id"]],
                legacy_self=[data["_self"]],
                creation_date=createdAt,
                update_date=updatedAt,
                created_by_id=created_by_id,
                updated_by_id=updated_by_id,
            )

            db.add(db_license)

        db.commit()


class ImportMTypeAnnotation(Import):
    name = "MTypeAnnotation"

    @staticmethod
    def is_correct_type(data):
        return "nsg:MType" in data.get("subClassOf", {})

    @staticmethod
    def ingest(
        db,
        project_context,
        data_list: list[dict],
        all_data_by_id: dict[str, dict],
        hierarchy_name: str,
    ):
        import_mtype_annotation_body(data_list, db)


class ImportETypeAnnotation(Import):
    name = "ETypeAnnotation"

    @staticmethod
    def is_correct_type(data):
        return "nsg:EType" in data.get("subClassOf", {})

    @staticmethod
    def ingest(
        db,
        project_context,
        data_list: list[dict],
        all_data_by_id: dict[str, dict],
        hierarchy_name: str,
    ):
        import_etype_annotation_body(data_list, db)


class ImportAnalysisSoftwareSourceCode(Import):
    name = "AnalysisSoftwareSourceCode"

    @staticmethod
    def is_correct_type(data):
        return "AnalysisSoftwareSourceCode" in ensurelist(data.get("@type", []))

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
                created_by_id=created_by_id,
                updated_by_id=updated_by_id,
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
        types = ensurelist(data.get("@type", []))
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
                created_by_id=created_by_id,
                updated_by_id=updated_by_id,
                creation_date=createdAt,
                update_date=updatedAt,
                authorized_project_id=project_context.project_id,
                authorized_public=AUTHORIZED_PUBLIC,
                exemplar_morphology_id=morphology.id,
            )

            db.add(db_emodel)

            db.flush()

            utils.import_ion_channel_models(
                configuration,
                db_emodel.id,
                all_data_by_id,
                project_context,
                hierarchy_name,
                db,
            )

            utils.import_contribution(
                data, db_emodel.id, db, created_by_id=created_by_id, updated_by_id=updated_by_id
            )

            # Import hoc file
            utils.import_distribution(
                emodel_script, db_emodel.id, EntityType.emodel, db, project_context
            )
            for annotation in ensurelist(data.get("annotation", [])):
                create_annotation(
                    annotation,
                    db_emodel.id,
                    db,
                    created_by_id=created_by_id,
                    updated_by_id=updated_by_id,
                )

        db.commit()


class ImportEModelDerivations(Import):
    name = "EModelWorkflow"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data.get("@type", []))
        return "EModelWorkflow" in types

    @staticmethod
    def ingest(
        db,
        project_context,
        data_list: list[dict],
        all_data_by_id: dict[str, dict],
        hierarchy_name: str,
    ):
        """Import emodel derivations from EModelWorkflow."""
        legacy_emodel_ids = set()
        derivations = {}
        for data in tqdm(data_list, desc="EModelWorkflow"):
            legacy_emodel_id = utils.find_id_in_entity(data, "EModel", "generates")
            legacy_etc_id = utils.find_id_in_entity(
                data, "ExtractionTargetsConfiguration", "hasPart"
            )
            if not legacy_emodel_id:
                L.warning("Not found EModel id in EModelWorkflow: {}", data["@id"])
                continue
            if not legacy_etc_id:
                L.warning(
                    "Not found ExtractionTargetsConfiguration id in EModelWorkflow: {}", data["@id"]
                )
                continue
            if not (etc := all_data_by_id.get(legacy_etc_id)):
                L.warning("Not found ExtractionTargetsConfiguration with id {}", legacy_etc_id)
                continue
            if not (legacy_trace_ids := list(utils.find_ids_in_entity(etc, "Trace", "uses"))):
                L.warning(
                    "Not found traces in ExtractionTargetsConfiguration with id {}", legacy_etc_id
                )
                continue
            if legacy_emodel_id in legacy_emodel_ids:
                L.warning("Duplicated and ignored traces for EModel id {}", legacy_emodel_id)
                continue
            legacy_emodel_ids.add(legacy_emodel_id)
            if not (emodel := utils._find_by_legacy_id(legacy_emodel_id, EModel, db)):
                L.warning("Not found EModel with legacy id {}", legacy_emodel_id)
                continue
            if emodel.id in derivations:
                L.warning("Duplicated and ignored traces for EModel uuid {}", emodel.id)
            derivations[emodel.id] = [
                utils._find_by_legacy_id(legacy_trace_id, ElectricalCellRecording, db).id
                for legacy_trace_id in legacy_trace_ids
            ]

        rows = [
            Derivation(used_id=trace_id, generated_id=emodel_id)
            for emodel_id, trace_ids in derivations.items()
            for trace_id in trace_ids
        ]
        L.info(
            "Imported derivations for {} EModels from {} records", len(derivations), len(data_list)
        )
        # delete everything from derivation table before adding the records
        query = sa.delete(Derivation)
        db.execute(query)
        db.add_all(rows)
        db.commit()


class ImportBrainAtlas(Import):
    name = "BrainAtlas"

    @staticmethod
    def is_correct_type(data):
        # for reasons unknown, the annotations are tagged as v1.2.0
        # the contents of the annotations is the same as in
        # s3://openbluebrain/Model_Data/Brain_atlas/Mouse/resolution_25_um/version_1.1.0/Annotation_volume/annotation_ccfv3_l23split_barrelsplit_validated.nrrd
        # but their sha256 hashes differ
        return (
            utils.is_type(data, "BrainParcellationMesh")
            and "atlasRelease" in data
            and data["atlasRelease"].get("tag") == "v1.1.0"
        ) or (
            utils.is_type(data, "BrainParcellationDataLayer")
            and "atlasRelease" in data
            and data["atlasRelease"].get("tag") == "v1.2.0"
        )

    @staticmethod
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name: str):
        meshes, annotations = [], []
        for d in data_list:
            if utils.is_type(d, "BrainParcellationMesh"):
                meshes.append(d)
            else:
                annotations.append(d)

        assert len(annotations) == 1
        brain_atlas = db.execute(
            sa.select(BrainAtlas).filter(BrainAtlas.name == BRAIN_ATLAS_NAME)
        ).scalar_one_or_none()
        if brain_atlas is None:
            hierarchy = db.execute(
                sa.select(BrainRegionHierarchy).filter(BrainRegionHierarchy.name == hierarchy_name)
            ).scalar_one()

            mouse = db.execute(
                sa.select(Species).filter(Species.name == "Mus musculus")
            ).scalar_one()

            admin = utils.get_or_create_admin(db)

            brain_atlas = BrainAtlas(
                name=BRAIN_ATLAS_NAME,
                description="version v1.1.0 from NEXUS",
                species_id=mouse.id,
                hierarchy_id=hierarchy.id,
                authorized_project_id=project_context.project_id,
                authorized_public=True,
                created_by_id=admin.id,
                updated_by_id=admin.id,
            )
            db.add(brain_atlas)
            db.commit()

            utils.import_distribution(
                annotations[0],
                brain_atlas.id,
                EntityType.brain_atlas,
                db,
                project_context,
            )

        for mesh in tqdm(meshes):
            brain_region_data = mesh["brainLocation"]["brainRegion"]
            brain_region_id = utils.get_brain_region_by_hier_id(
                brain_region_data, hierarchy_name, db
            )

            atlas_region = db.execute(
                sa.select(BrainAtlasRegion).filter(
                    BrainAtlasRegion.brain_region_id == str(brain_region_id)
                )
            ).scalar_one_or_none()

            if atlas_region is None:
                annotation_id = curate.curate_brain_region(brain_region_data)["@id"]
                volume = None

                is_leaf_region = False
                if annotation_id in BRAIN_ATLAS_REGION_VOLUMES:
                    volume = BRAIN_ATLAS_REGION_VOLUMES[annotation_id]
                    is_leaf_region = True

                created_by_id, updated_by_id = utils.get_agent_mixin(mesh, db)

                atlas_region = BrainAtlasRegion(
                    brain_atlas_id=brain_atlas.id,
                    brain_region_id=brain_region_id,
                    volume=volume,
                    is_leaf_region=is_leaf_region,
                    authorized_project_id=project_context.project_id,
                    authorized_public=True,
                    created_by_id=created_by_id,
                    updated_by_id=updated_by_id,
                )
                db.add(atlas_region)
                db.commit()

            utils.import_distribution(
                mesh, atlas_region.id, EntityType.brain_atlas, db, project_context
            )


class ImportMorphologies(Import):
    name = "Morphologies"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data.get("@type", []))
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
            brain_location = utils.get_brain_location(data)
            license_id = utils.get_license_mixin(data, db)
            species_id, strain_id = utils.get_species_mixin(data, db)
            createdAt, updatedAt = utils.get_created_and_updated(data)
            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)

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
                created_by_id=created_by_id,
                updated_by_id=updated_by_id,
            )

            db.add(db_reconstruction_morphology)
            db.commit()
            db.refresh(db_reconstruction_morphology)

            utils.import_contribution(
                data, db_reconstruction_morphology.id, db, created_by_id, updated_by_id
            )

            for annotation in ensurelist(data.get("annotation", [])):
                create_annotation(
                    annotation, db_reconstruction_morphology.id, db, created_by_id, updated_by_id
                )


class ImportExperimentalNeuronDensities(Import):
    name = "ExperimentalNeuronDensities"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data.get("@type", []))
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
        types = ensurelist(data.get("@type", []))
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
        types = ensurelist(data.get("@type", []))
        return "ExperimentalSynapsesPerConnection" in types

    @staticmethod
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name: str):
        _import_experimental_densities(
            db,
            project_context,
            ExperimentalSynapsesPerConnection,
            curate.curate_synapses_per_connections,
            hierarchy_name=hierarchy_name,
            data_list=data_list,
        )


class ImportElectricalCellRecording(Import):
    name = "SingleCellExperimentalTrace"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data.get("@type", []))
        return (
            "SingleCellExperimentalTrace" in types
            or "Trace" in types
            or "ExperimentalTrace" in types
        )

    @staticmethod
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name):
        for data in tqdm(data_list):
            legacy_id = data["@id"]
            legacy_self = data["_self"]

            rm = utils._find_by_legacy_id(legacy_id, ElectricalCellRecording, db)
            if rm:
                continue

            data = curate.curate_trace(data)
            distributions = ensurelist(data.get("distribution", []))

            # register resources that have at least one supported file
            if not (
                has_content_type_in_distributions(ContentType.nwb, distributions)
                or has_content_type_in_distributions(ContentType.h5, distributions)
            ):
                continue

            brain_region_id = utils.get_brain_region(data, hierarchy_name, db)

            license_id = utils.get_license_mixin(data, db)
            subject_id = utils.get_or_create_subject(data, project_context, db)
            createdAt, updatedAt = utils.get_created_and_updated(data)
            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)

            age = data.get("subject", {}).get("age", {}).get("value", None)
            comment = data.get("note", None)

            if "ExperimentalTrace" in data.get("@type", []):
                recording_origin = ElectricalRecordingOrigin.in_vitro
            elif "SimulationTrace" in data.get("@type", []):
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
                created_by_id=created_by_id,
                updated_by_id=updated_by_id,
            )

            db.add(db_item)
            db.commit()
            db.refresh(db_item)

            utils.import_contribution(data, db_item.id, db, created_by_id, updated_by_id)

            for annotation in ensurelist(data.get("annotation", [])):
                create_annotation(annotation, db_item.id, db, created_by_id, updated_by_id)

            for stimulus in ensurelist(data.get("stimulus", [])):
                stimulus_type = stimulus["stimulusType"]
                if "@id" in stimulus_type and stimulus_type["@id"] in all_data_by_id:
                    stimulus_type = all_data_by_id[stimulus_type["@id"]]

                # create a stimulus for each stimulus in the data
                utils.create_stimulus(
                    stimulus_type, db_item.id, project_context, db, created_by_id, updated_by_id
                )


def has_content_type_in_distributions(content_type: ContentType, distributions: list) -> bool:
    """Return True if the content_type is present in the distributions."""
    return content_type in {d["encodingFormat"] for d in distributions}


class ImportMEModel(Import):
    name = "MEModel"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data.get("@type", []))
        return "MEModel" in types or "https://neuroshapes.org/MEModel" in types

    @staticmethod
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name: str):
        for data in tqdm(data_list):
            legacy_id = data["@id"]
            legacy_self = data["_self"]
            rm = utils._find_by_legacy_id(legacy_id, MEModel, db)
            if rm:
                continue
            hierarchy_name = curate.curate_hierarchy_name(hierarchy_name)
            brain_region_id = utils.get_brain_region(data, hierarchy_name, db)

            morphology_id = utils.find_part_id(data, "NeuronMorphology")
            morphology = utils._find_by_legacy_id(morphology_id, ReconstructionMorphology, db)

            emodel_id = utils.find_part_id(data, "EModel")
            if (
                emodel_id
                == "https://bbp.epfl.ch/data/bbp/mmb-point-neuron-framework-model/396071d5-9c99-4103-9a25-90c500d969c9"
            ):
                L.info(
                    "Skipping memodel {} , because emodel with id: {} is deprecated".format(
                        legacy_id, emodel_id
                    )
                )
                continue
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
                created_by_id=created_by_id,
                updated_by_id=updated_by_id,
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
            db_calibration = MEModelCalibrationResult(
                calibrated_entity_id=db_item.id,
                holding_current=data.get("holding_current", 0),
                threshold_current=data.get("threshold_current", 0),
                authorized_project_id=project_context.project_id,
                authorized_public=AUTHORIZED_PUBLIC,
                created_by_id=created_by_id,
                updated_by_id=updated_by_id,
                creation_date=createdAt,
                update_date=updatedAt,
            )
            db.add(db_calibration)
            db.flush()
            utils.import_contribution(data, db_item.id, db, created_by_id, updated_by_id)

            for annotation in ensurelist(data.get("annotation", [])):
                create_annotation(annotation, db_item.id, db, created_by_id, updated_by_id)

        db.commit()


class ImportSingleNeuronSimulation(Import):
    name = "SingleNeuronSimulation"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data.get("@type", []))
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
            if (
                me_model_lid
                == "https://bbp.epfl.ch/data/bbp/mmb-point-neuron-framework-model/1b89d6a2-3d6e-4530-a4af-6752412987ea"
            ):
                L.info(
                    "Skipping SingleNeuronSimulation {} because it uses deprecated MEModel {}".format(
                        legacy_id, me_model_lid
                    )
                )
                continue
            if not me_model:
                # many MEModel deprecated because of https://bbp.epfl.ch/data/bbp/mmb-point-neuron-framework-model/396071d5-9c99-4103-9a25-90c500d969c9
                L.info(
                    "SingleNeuronSimulation {} uses MEModel {}, but it is not found in the database.".format(
                        legacy_id, me_model_lid
                    )
                )
                continue

            rm = SingleNeuronSimulation(
                legacy_id=[legacy_id],
                legacy_self=[legacy_self],
                name=data.get("name", None),
                description=data.get("description", None),
                # seed became mandatory
                seed=data.get("seed", 0),
                status=data.get("status", "unknown"),
                injection_location=data.get("injectionLocation")
                or data.get("injection_location"),  # TODO: Get from config file if not existent?
                recording_location=data.get("recordingLocation") or data.get("recording_location"),
                me_model_id=me_model.id,
                brain_region_id=brain_region_id,
                created_by_id=created_by_id,
                updated_by_id=updated_by_id,
                authorized_project_id=project_context.project_id,
                authorized_public=AUTHORIZED_PUBLIC,
            )
            db.add(rm)
        db.commit()


class ImportMETypeDensity(Import):
    name = "METypeDensity"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data.get("@type", []))
        return "METypeDensity" in types or "NeuronDensity" in types

    @staticmethod
    def ingest(
        db: Session,
        project_context: ProjectContext,
        data_list: list[dict],
        all_data_by_id: dict,
        hierarchy_name: str,
    ):
        for data in tqdm(data_list):
            if not ("atlasRelease" in data and data["atlasRelease"]["@id"] == BRAIN_ATLAS_ID):
                continue

            legacy_id, legacy_self = data["@id"], data["_self"]
            rm = utils._find_by_legacy_id(legacy_id, METypeDensity, db)
            if rm:
                continue

            brain_region_id = utils.get_brain_region(data, hierarchy_name, db)

            createdAt, updatedAt = utils.get_created_and_updated(data)
            created_by_id, updated_by_id = utils.get_agent_mixin(data, db)

            species_id, strain_id = utils.get_species_mixin(data, db)

            db_item = METypeDensity(
                legacy_id=[legacy_id],
                legacy_self=[legacy_self],
                name=data.get("name", None),
                description=data.get("description", ""),
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=strain_id,
                created_by_id=created_by_id,
                updated_by_id=updated_by_id,
                creation_date=createdAt,
                update_date=updatedAt,
                authorized_project_id=project_context.project_id,
                authorized_public=AUTHORIZED_PUBLIC,
            )
            db.add(db_item)
            db.flush()

            utils.import_contribution(data, db_item.id, db, created_by_id, updated_by_id)

            for annotation in ensurelist(data.get("annotation", [])):
                create_annotation(annotation, db_item.id, db, created_by_id, updated_by_id)

        db.commit()


class ImportCellComposition(Import):
    name = "Cell Composition"

    @staticmethod
    def is_correct_type(data):
        return (
            "CellComposition" in ensurelist(data.get("@type", []))
            and data.get("@id", "") == CELL_COMPOSITION_ID
        )

    @staticmethod
    def ingest(
        db: Session,
        project_context: ProjectContext,
        data_list: list[dict],
        all_data_by_id: dict,
        hierarchy_name: str,
    ):
        for data in tqdm(data_list):
            legacy_id, legacy_self = data["@id"], data["_self"]
            rm = utils._find_by_legacy_id(legacy_id, METypeDensity, db)
            if rm:
                continue

            brain_region_id = utils.get_brain_region(data, hierarchy_name, db)

            try:
                created_by_id, updated_by_id = utils.get_agent_mixin(data, db)
            except RuntimeError as e:
                msg = f"Agent not found.: {e}"
                L.warning(msg)
                created_by_id = updated_by_id = None

            createdAt, updatedAt = utils.get_created_and_updated(data)

            species_id, strain_id = utils.get_species_mixin(data, db)

            # graft summary and volumes distributions to CellComposition to later
            # add them as assets instead of linked resources.
            summary = all_data_by_id[data["cellCompositionSummary"]["@id"]]["distribution"]
            volumes = all_data_by_id[data["cellCompositionVolume"]["@id"]]["distribution"]

            assert "distribution" not in all_data_by_id[legacy_id]
            all_data_by_id[legacy_id]["distribution"] = [summary, volumes]

            db_item = CellComposition(
                legacy_id=[legacy_id],
                legacy_self=[legacy_self],
                name=data.get("name", "CellComposition"),
                description=data.get("description", ""),
                brain_region_id=brain_region_id,
                species_id=species_id,
                strain_id=strain_id,
                created_by_id=created_by_id,
                updated_by_id=updated_by_id,
                creation_date=createdAt,
                update_date=updatedAt,
                authorized_project_id=project_context.project_id,
                authorized_public=AUTHORIZED_PUBLIC,
            )
            db.add(db_item)
            db.flush()

            utils.import_contribution(data, db_item.id, db, created_by_id, updated_by_id)

            for annotation in ensurelist(data.get("annotation", [])):
                create_annotation(annotation, db_item.id, db, created_by_id, updated_by_id)


class ImportDistribution(Import):
    name = "Distribution"

    @staticmethod
    def is_correct_type(data):
        return (
            "distribution" in data
            and not utils.is_type(data, "SubCellularModelScript")
            and not utils.is_type(data, "License")
        )

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
            if root := utils._find_by_legacy_id(legacy_id, Entity, db):
                utils.import_distribution(data, root.id, root.type, db, project_context)
            else:
                dt = data.get("@type", [])
                types = tuple(sorted(dt)) if isinstance(dt, list) else (dt,)
                ignored[types] += 1

        if ignored:
            L.warning("Ignored assets by type: {}", ignored)


class ImportNeuronMorphologyFeatureAnnotation(Import):
    name = "NeuronMorphologyFeatureAnnotation"

    @staticmethod
    def is_correct_type(data):
        types = ensurelist(data.get("@type", []))
        return "NeuronMorphologyFeatureAnnotation" in types

    @staticmethod
    def ingest(db, project_context, data_list, all_data_by_id, hierarchy_name: str):
        annotations = defaultdict(list)
        info = {
            "newly_registered": 0,
            "already_registered": 0,
            "missing_morphology_id": 0,
            "missing_morphology": 0,
            "duplicate_annotation": 0,
        }
        for data in tqdm(data_list):
            morphology_legacy_id = data.get("hasTarget", {}).get("hasSource", {}).get("@id", None)
            if not morphology_legacy_id:
                print("Skipping morphology feature annotation due to missing legacy id.")
                info["missing_morphology_id"] += 1
                continue

            legacy_id = data["@id"]
            legacy_self = data["_self"]
            db_element = utils._find_by_legacy_id(legacy_id, MeasurementAnnotation, db)
            if db_element:
                info["already_registered"] += 1
                continue

            rm = utils._find_by_legacy_id(morphology_legacy_id, ReconstructionMorphology, db)
            if not rm:
                info["missing_morphology"] += 1
                continue

            if (
                db.query(MeasurementAnnotation.id)
                .where(MeasurementAnnotation.entity_id == rm.id)
                .first()
            ):
                info["already_registered"] += 1
                continue

            # compartment can be at the top level, or in each element of hasBody
            compartment = data.get("compartment")
            measurement_kinds = []
            for measurement in data.get("hasBody", []):
                measurement_items = []
                for item in ensurelist(measurement.get("value", {}).get("series", [])):
                    if measurement_item := build_measurement_item(item):
                        measurement_items.append(measurement_item)
                if measurement_kind := build_measurement_kind(
                    measurement, measurement_items=measurement_items, compartment=compartment
                ):
                    measurement_kinds.append(measurement_kind)

            createdAt, updatedAt = utils.get_created_and_updated(data)

            annotations[rm.id].append(
                MeasurementAnnotation(
                    entity_id=rm.id,
                    creation_date=createdAt,
                    update_date=updatedAt,
                    legacy_id=[legacy_id],
                    legacy_self=[legacy_self],
                    measurement_kinds=measurement_kinds,
                    created_by_id=rm.created_by_id,
                    updated_by_id=rm.updated_by_id,
                )
            )

        for entity_id, entity_annotations in tqdm(annotations.items()):
            if len(entity_annotations) > 1:
                info["duplicate_annotation"] += len(entity_annotations) - 1
                entity_annotation = merge_measurements_annotations(
                    entity_annotations,
                    entity_id,
                    entity_annotations[0].created_by_id,
                    entity_annotations[0].updated_by_id,
                )
            else:
                entity_annotation = entity_annotations[0]
            info["newly_registered"] += 1
            db.add(entity_annotation)

        db.commit()

        L.warning(
            "NeuronMorphologyFeatureAnnotation report:\n"
            "    Annotations not related to any morphology: {}\n"
            "    Annotations related to a morphology that isn't registered: {}\n"
            "    Annotations related to a morphology that has already an annotation: {}\n"
            "    Duplicate_annotation: {}\n"
            "    Newly registered: {}",
            info["missing_morphology_id"],
            info["missing_morphology"],
            info["already_registered"],
            info["duplicate_annotation"],
            info["newly_registered"],
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
        created_by_id, updated_by_id = utils.get_agent_mixin(data, db)

        createdAt, updatedAt = utils.get_created_and_updated(data)

        kwargs = {
            "legacy_id": [legacy_id],
            "legacy_self": [legacy_self],
            "name": data.get("name"),
            "description": data.get("description", ""),
            "subject_id": subject_id,
            "license_id": license_id,
            "brain_region_id": brain_region_id,
            "created_by_id": created_by_id,
            "updated_by_id": updated_by_id,
            "creation_date": createdAt,
            "update_date": updatedAt,
            "authorized_project_id": project_context.project_id,
            "authorized_public": AUTHORIZED_PUBLIC,
        }

        if model_type is ExperimentalSynapsesPerConnection:
            try:
                (
                    kwargs["pre_mtype_id"],
                    kwargs["post_mtype_id"],
                    kwargs["pre_region_id"],
                    kwargs["post_region_id"],
                ) = utils.get_synaptic_pathway(data["synapticPathway"], hierarchy_name, db)
            except Exception as e:
                msg = f"Failed to create synaptic pathway: {data['synapticPathway']}.\nReason: {e}"
                L.warning(msg)
                continue

        db_item = model_type(**kwargs)
        db.add(db_item)
        db.commit()
        utils.import_contribution(data, db_item.id, db, created_by_id, updated_by_id)

        for annotation in ensurelist(data.get("annotation", [])):
            create_annotation(annotation, db_item.id, db, created_by_id, updated_by_id)

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
    importers = [
        ImportAgent,
        ImportSpecies,
        ImportLicense,
        ImportMTypeAnnotation,
        ImportETypeAnnotation,
        ImportMETypeDensity,
        ImportCellComposition,
        ImportAnalysisSoftwareSourceCode,
        ImportMorphologies,
        ImportEModels,
        ImportExperimentalNeuronDensities,
        ImportExperimentalBoutonDensity,
        ImportExperimentalSynapsesPerConnection,
        ImportMEModel,
        ImportElectricalCellRecording,
        ImportSingleNeuronSimulation,
        ImportBrainAtlas,
        ImportDistribution,
        ImportNeuronMorphologyFeatureAnnotation,
        ImportEModelDerivations,
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
        # Note: Allowing the data list to be collected here before each importer's execution allows
        # moving parts of one resource to another. For example, distributions of linked
        # resources can be grafted to the parent to avoid having too many entities. To do so,
        # the order of the importer execution matters.
        data_list = [d for d in all_data_by_id.values() if importer.is_correct_type(d)]

        print(f"Ingesting {importer.name}")

        importer.ingest(
            db,
            project_context,
            data_list,
            all_data_by_id=all_data_by_id,
            hierarchy_name=hierarchy_name,
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
        admin = utils.get_or_create_admin(db)

        hier = (
            db.query(BrainRegionHierarchy)
            .filter(BrainRegionHierarchy.name == hierarchy_name)
            .first()
        )

        if not hier:
            hier = BrainRegionHierarchy(
                name=hierarchy_name, created_by_id=admin.id, updated_by_id=admin.id
            )
            db.add(hier)
            db.flush()

        ids = {
            v.annotation_value: v.id
            for v in db.execute(
                sa.select(BrainRegion.id, BrainRegion.annotation_value).where(
                    BrainRegion.hierarchy_id == hier.id
                )
            ).all()
        }
        ids[None] = None

        for region in tqdm(reversed(regions), total=len(regions)):
            if region["id"] in ids:
                continue

            db_br = BrainRegion(
                annotation_value=region["id"],
                name=region["name"],
                acronym=region["acronym"],
                parent_structure_id=ids[region["parent_structure_id"]],
                color_hex_triplet=region["color_hex_triplet"],
                hierarchy_id=hier.id,
                created_by_id=admin.id,
                updated_by_id=admin.id,
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


@cli.command()
@click.argument("input_digest_path", type=REQUIRED_PATH)
@click.argument("output_digest_path")
@click.option("--out-dir", type=Path, help="Output directory for curated files.")
@click.option("--dry-run", is_flag=True, help="Run curation without modifying db assets.")
def curate_files(input_digest_path, output_digest_path, out_dir, dry_run):
    assert out_dir.exists()

    with Path(input_digest_path).open("r", encoding="utf-8") as f:
        src_paths = dict(line.strip().split(" ", maxsplit=1) for line in f)

    with (
        closing(configure_database_session_manager()) as database_session_manager,
        database_session_manager.session() as db,
    ):
        # Group assets by entity_type/entity_id/content_type
        assets_per_entity_type = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for asset in db.query(Asset).all():
            entity_type = asset.full_path.split("/")[4]
            assets_per_entity_type[entity_type][asset.entity_id][asset.content_type].append(asset)

        if not assets_per_entity_type:
            raise RuntimeError("No assets found. Please run 'make import' to import distributions.")

        config = {
            EntityType.electrical_cell_recording: electrical_cell_recording.curate_assets,
            EntityType.cell_composition: cell_composition.curate_assets,
        }

        new_src_paths = {}
        for entity_type, curator in config.items():
            if not (assets_per_entity := assets_per_entity_type.get(entity_type)):
                continue

            print(f"Curating: {entity_type}")
            for entity_id, assets in tqdm(assets_per_entity.items()):
                try:
                    new_src_paths |= curator(
                        db=db,
                        src_paths=src_paths,
                        assets=assets,
                        out_dir=out_dir,
                        is_dry_run=dry_run,
                    )
                except Exception as e:
                    msg = f"Failed curation for entity {entity_type}: {entity_id}. Reason : {e}"
                    L.warning(msg)
                    continue

                db.commit()

    all_paths = src_paths | new_src_paths
    with open(output_digest_path, "w") as fp:
        for digest, path in all_paths.items():
            fp.write(f"{digest} {path}\n")


if __name__ == "__main__":
    cli()
