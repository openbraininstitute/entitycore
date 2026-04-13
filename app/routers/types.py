from enum import StrEnum, auto
from typing import TYPE_CHECKING

from app.utils.enum import HyphenStrEnum, combine_str_enums


class EntityRoute(HyphenStrEnum):
    """Entity routes.

    Note: There are fewer routes than entity types
    """

    brain_atlas = auto()
    brain_atlas_region = auto()
    cell_composition = auto()
    cell_morphology = auto()
    cell_morphology_protocol = auto()
    electrical_cell_recording = auto()
    electrical_recording_stimulus = auto()
    emodel = auto()
    experimental_bouton_density = auto()
    experimental_neuron_density = auto()
    experimental_synapses_per_connection = auto()
    external_url = auto()
    ion_channel_model = auto()
    ion_channel_modeling_campaign = auto()
    ion_channel_modeling_config = auto()
    ion_channel_recording = auto()
    memodel = auto()
    memodel_calibration_result = auto()
    simulation = auto()
    simulation_campaign = auto()
    simulation_result = auto()
    single_neuron_simulation = auto()
    single_neuron_synaptome = auto()
    single_neuron_synaptome_simulation = auto()
    subject = auto()
    validation_result = auto()
    circuit = auto()
    circuit_extraction_campaign = auto()
    circuit_extraction_config = auto()
    em_dense_reconstruction_dataset = auto()
    em_cell_mesh = auto()
    analysis_notebook_template = auto()
    analysis_notebook_environment = auto()
    analysis_notebook_result = auto()
    skeletonization_config = auto()
    skeletonization_campaign = auto()
    task_config = auto()


class GlobalRoute(HyphenStrEnum):
    """Global resource routes."""

    brain_region_hierarchy = auto()
    brain_region = auto()
    species = auto()
    strain = auto()
    license = auto()
    mtype = auto()
    etype = auto()
    publication = auto()
    role = auto()
    ion_channel = auto()
    measurement_annotation = auto()
    measurement_label = auto()


class AssociationRoute(HyphenStrEnum):
    """Association routes."""

    etype_classification = auto()
    mtype_classification = auto()
    contribution = auto()
    derivation = auto()
    scientific_artifact_publication_link = auto()
    scientific_artifact_external_url_link = auto()


class AgentRoute(HyphenStrEnum):
    """Agent routes."""

    person = auto()
    organization = auto()
    consortium = auto()


class ActivityRoute(HyphenStrEnum):
    """Activity routes."""

    simulation_execution = auto()
    simulation_generation = auto()
    validation = auto()
    calibration = auto()
    analysis_notebook_execution = auto()
    ion_channel_modeling_execution = auto()
    ion_channel_modeling_config_generation = auto()
    circuit_extraction_config_generation = auto()
    circuit_extraction_execution = auto()
    skeletonization_execution = auto()
    skeletonization_config_generation = auto()
    task_activity = auto()


if TYPE_CHECKING:
    ResourceRoute = StrEnum
else:
    ResourceRoute = combine_str_enums(
        "ResourceRoute", (EntityRoute, AssociationRoute, GlobalRoute, AgentRoute, ActivityRoute)
    )
