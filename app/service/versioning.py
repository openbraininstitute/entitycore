"""Generic versioning service."""

import functools
import operator
import uuid
from http import HTTPStatus
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy_history import version_class

from app.db.auth import constrain_to_accessible_entities
from app.db.utils import RESOURCE_TYPE_TO_CLASS, get_declaring_class, has_project_id_in_columns
from app.dependencies.auth import UserContextDep
from app.dependencies.db import SessionDep
from app.errors import ApiError, ApiErrorCode, ensure_result
from app.schemas.agent import ConsortiumRead, OrganizationRead, PersonRead
from app.schemas.analysis_notebook_environment import AnalysisNotebookEnvironmentRead
from app.schemas.analysis_notebook_execution import AnalysisNotebookExecutionRead
from app.schemas.analysis_notebook_result import AnalysisNotebookResultRead
from app.schemas.analysis_notebook_template import AnalysisNotebookTemplateRead
from app.schemas.annotation import ETypeClassRead, MTypeClassRead
from app.schemas.auth import UserContext
from app.schemas.base import LicenseRead
from app.schemas.brain_atlas import BrainAtlasRead
from app.schemas.brain_atlas_region import BrainAtlasRegionRead
from app.schemas.brain_region import BrainRegionRead
from app.schemas.brain_region_hierarchy import BrainRegionHierarchyRead
from app.schemas.calibration import CalibrationRead
from app.schemas.cell_composition import CellCompositionRead
from app.schemas.cell_morphology import CellMorphologyRead
from app.schemas.cell_morphology_protocol import CellMorphologyProtocolRead
from app.schemas.circuit import CircuitRead
from app.schemas.circuit_extraction_campaign import CircuitExtractionCampaignRead
from app.schemas.circuit_extraction_config import CircuitExtractionConfigRead
from app.schemas.circuit_extraction_config_generation import CircuitExtractionConfigGenerationRead
from app.schemas.circuit_extraction_execution import CircuitExtractionExecutionRead
from app.schemas.classification import ETypeClassificationRead, MTypeClassificationRead
from app.schemas.contribution import ContributionRead
from app.schemas.density import (
    ExperimentalBoutonDensityRead,
    ExperimentalNeuronDensityRead,
    ExperimentalSynapsesPerConnectionRead,
)
from app.schemas.derivation import DerivationRead
from app.schemas.electrical_cell_recording import ElectricalCellRecordingRead
from app.schemas.electrical_recording_stimulus import ElectricalRecordingStimulusRead
from app.schemas.em_cell_mesh import EMCellMeshRead
from app.schemas.em_dense_reconstruction_dataset import EMDenseReconstructionDatasetRead
from app.schemas.emodel import EModelRead
from app.schemas.external_url import ExternalUrlRead
from app.schemas.ion_channel import IonChannelRead
from app.schemas.ion_channel_model import IonChannelModelRead
from app.schemas.ion_channel_modeling_campaign import IonChannelModelingCampaignRead
from app.schemas.ion_channel_modeling_config import IonChannelModelingConfigRead
from app.schemas.ion_channel_modeling_config_generation import (
    IonChannelModelingConfigGenerationRead,
)
from app.schemas.ion_channel_modeling_execution import IonChannelModelingExecutionRead
from app.schemas.ion_channel_recording import IonChannelRecordingRead
from app.schemas.me_model import MEModelRead
from app.schemas.measurement_annotation import MeasurementAnnotationRead
from app.schemas.measurement_label import MeasurementLabelRead
from app.schemas.memodel_calibration_result import MEModelCalibrationResultRead
from app.schemas.publication import PublicationRead
from app.schemas.role import RoleRead
from app.schemas.scientific_artifact import ScientificArtifactRead
from app.schemas.scientific_artifact_external_url_link import ScientificArtifactExternalUrlLinkRead
from app.schemas.scientific_artifact_publication_link import ScientificArtifactPublicationLinkRead
from app.schemas.simulation import (
    SimulationRead,
    SingleNeuronSimulationRead,
    SingleNeuronSynaptomeSimulationRead,
)
from app.schemas.simulation_campaign import SimulationCampaignRead
from app.schemas.simulation_execution import SimulationExecutionRead
from app.schemas.simulation_generation import SimulationGenerationRead
from app.schemas.simulation_result import SimulationResultRead
from app.schemas.skeletonization_campaign import SkeletonizationCampaignRead
from app.schemas.skeletonization_config import SkeletonizationConfigRead
from app.schemas.skeletonization_config_generation import SkeletonizationConfigGenerationRead
from app.schemas.skeletonization_execution import SkeletonizationExecutionRead
from app.schemas.species import SpeciesRead, StrainRead
from app.schemas.subject import SubjectRead
from app.schemas.synaptome import SingleNeuronSynaptomeRead
from app.schemas.validation import ValidationRead, ValidationResultRead
from app.utils.routers import ResourceRoute, route_to_type

RESOURCE_TYPE_TO_READ_SCHEMA = {
    "analysis_notebook_environment": AnalysisNotebookEnvironmentRead,
    "analysis_notebook_execution": AnalysisNotebookExecutionRead,
    "analysis_notebook_result": AnalysisNotebookResultRead,
    "analysis_notebook_template": AnalysisNotebookTemplateRead,
    "brain_atlas": BrainAtlasRead,
    "brain_atlas_region": BrainAtlasRegionRead,
    "brain_region": BrainRegionRead,
    "brain_region_hierarchy": BrainRegionHierarchyRead,
    "calibration": CalibrationRead,
    "cell_composition": CellCompositionRead,
    "cell_morphology": CellMorphologyRead,
    "cell_morphology_protocol": CellMorphologyProtocolRead,
    "circuit": CircuitRead,
    "circuit_extraction_campaign": CircuitExtractionCampaignRead,
    "circuit_extraction_config": CircuitExtractionConfigRead,
    "circuit_extraction_config_generation": CircuitExtractionConfigGenerationRead,
    "circuit_extraction_execution": CircuitExtractionExecutionRead,
    "consortium": ConsortiumRead,
    "contribution": ContributionRead,
    "derivation": DerivationRead,
    "electrical_cell_recording": ElectricalCellRecordingRead,
    "electrical_recording_stimulus": ElectricalRecordingStimulusRead,
    "em_cell_mesh": EMCellMeshRead,
    "em_dense_reconstruction_dataset": EMDenseReconstructionDatasetRead,
    "emodel": EModelRead,
    "etype_class": ETypeClassRead,
    "etype_classification": ETypeClassificationRead,
    "experimental_bouton_density": ExperimentalBoutonDensityRead,
    "experimental_neuron_density": ExperimentalNeuronDensityRead,
    "experimental_synapses_per_connection": ExperimentalSynapsesPerConnectionRead,
    "external_url": ExternalUrlRead,
    "ion_channel": IonChannelRead,
    "ion_channel_model": IonChannelModelRead,
    "ion_channel_modeling_campaign": IonChannelModelingCampaignRead,
    "ion_channel_modeling_config": IonChannelModelingConfigRead,
    "ion_channel_modeling_config_generation": IonChannelModelingConfigGenerationRead,
    "ion_channel_modeling_execution": IonChannelModelingExecutionRead,
    "ion_channel_recording": IonChannelRecordingRead,
    "license": LicenseRead,
    "measurement_annotation": MeasurementAnnotationRead,
    "measurement_label": MeasurementLabelRead,
    "memodel": MEModelRead,
    "memodel_calibration_result": MEModelCalibrationResultRead,
    "mtype_class": MTypeClassRead,
    "mtype_classification": MTypeClassificationRead,
    "organization": OrganizationRead,
    "person": PersonRead,
    "publication": PublicationRead,
    "role": RoleRead,
    "scientific_artifact": ScientificArtifactRead,
    "scientific_artifact_external_url_link": ScientificArtifactExternalUrlLinkRead,
    "scientific_artifact_publication_link": ScientificArtifactPublicationLinkRead,
    "simulation": SimulationRead,
    "simulation_campaign": SimulationCampaignRead,
    "simulation_execution": SimulationExecutionRead,
    "simulation_generation": SimulationGenerationRead,
    "simulation_result": SimulationResultRead,
    "single_neuron_simulation": SingleNeuronSimulationRead,
    "single_neuron_synaptome": SingleNeuronSynaptomeRead,
    "single_neuron_synaptome_simulation": SingleNeuronSynaptomeSimulationRead,
    "skeletonization_campaign": SkeletonizationCampaignRead,
    "skeletonization_config": SkeletonizationConfigRead,
    "skeletonization_config_generation": SkeletonizationConfigGenerationRead,
    "skeletonization_execution": SkeletonizationExecutionRead,
    "species": SpeciesRead,
    "strain": StrainRead,
    "subject": SubjectRead,
    "validation": ValidationRead,
    "validation_result": ValidationResultRead,
}

ResourceTypeUnion = functools.reduce(operator.or_, RESOURCE_TYPE_TO_READ_SCHEMA.values())


def _get_version_count(
    db: Session,
    user_context: UserContext,
    db_model_version_class: Any,
    resource_id: uuid.UUID,
) -> int:
    base_query = sa.select(db_model_version_class).where(db_model_version_class.id == resource_id)
    if has_project_id_in_columns(db_model_version_class):
        base_query = constrain_to_accessible_entities(
            base_query, project_id=user_context.project_id, db_model_class=db_model_version_class
        )
    total_versions = db.execute(
        base_query.with_only_columns(
            sa.func.count(sa.func.distinct(db_model_version_class.transaction_id)).label("count")
        )
    ).scalar_one()
    return total_versions


def _get_version_model(
    db: Session,
    user_context: UserContext,
    db_model_version_class: Any,
    resource_id: uuid.UUID,
    version_num: int,
) -> Any:
    base_query = sa.select(db_model_version_class).where(db_model_version_class.id == resource_id)
    if id_model_class := get_declaring_class(db_model_version_class, "authorized_project_id"):
        base_query = constrain_to_accessible_entities(
            base_query, project_id=user_context.project_id, db_model_class=id_model_class
        )
    if version_num < 0:
        count_query = base_query.with_only_columns(
            sa.func.count(sa.func.distinct(db_model_version_class.transaction_id)).label("count")
        )
        total_versions = db.execute(count_query).scalar_one()
        version_num += total_versions
    if version_num < 0:
        raise ApiError(
            message="Version not found",
            error_code=ApiErrorCode.ENTITY_NOT_FOUND,
            http_status_code=HTTPStatus.NOT_FOUND,
        )
    select_query = (
        base_query.order_by(db_model_version_class.transaction_id).offset(version_num).limit(1)
    )
    with ensure_result(error_message="Version not found"):
        db_model = db.execute(select_query).scalar_one()
    return db_model


def get_version_count(
    db: SessionDep,
    user_context: UserContextDep,
    resource_route: ResourceRoute,
    resource_id: uuid.UUID,
) -> int:
    """Return the number fo versions."""
    resource_type = route_to_type(resource_route)
    db_model_class = RESOURCE_TYPE_TO_CLASS[resource_type]
    db_model_version_class: Any = version_class(db_model_class)
    return _get_version_count(
        db=db,
        user_context=user_context,
        db_model_version_class=db_model_version_class,
        resource_id=resource_id,
    )


def get_version_model(
    db: SessionDep,
    user_context: UserContextDep,
    resource_route: ResourceRoute,
    resource_id: uuid.UUID,
    version_num: int,
) -> ResourceTypeUnion:  # pyright: ignore[reportInvalidTypeForm]
    """Return a specific version of a resource."""
    resource_type = route_to_type(resource_route)
    db_model_class = RESOURCE_TYPE_TO_CLASS[resource_type]
    db_model_version_class: Any = version_class(db_model_class)
    db_model = _get_version_model(
        db=db,
        user_context=user_context,
        db_model_version_class=db_model_version_class,
        resource_id=resource_id,
        version_num=version_num,
    )
    read_schema_class = RESOURCE_TYPE_TO_READ_SCHEMA[resource_type]
    return read_schema_class.model_validate(db_model)


def get_version_changeset(
    db: SessionDep,
    user_context: UserContextDep,
    resource_route: ResourceRoute,
    resource_id: uuid.UUID,
    version_num: int,
) -> dict[str, list]:
    """Return the set of changed attributes for a specific version of a resource."""
    resource_type = route_to_type(resource_route)
    db_model_class = RESOURCE_TYPE_TO_CLASS[resource_type]
    db_model_version_class: Any = version_class(db_model_class)
    db_model = _get_version_model(
        db=db,
        user_context=user_context,
        db_model_version_class=db_model_version_class,
        resource_id=resource_id,
        version_num=version_num,
    )
    return db_model.changeset
