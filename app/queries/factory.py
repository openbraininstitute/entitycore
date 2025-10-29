from typing import Any, cast

from app.db.model import (
    Agent,
    BrainRegion,
    CellMorphology,
    CellMorphologyProtocol,
    Circuit,
    Contribution,
    EMDenseReconstructionDataset,
    EModel,
    Entity,
    ETypeClass,
    ETypeClassification,
    Generation,
    Identifiable,
    IonChannel,
    IonChannelModel,
    IonChannelModelingConfig,
    IonChannelModelToEModel,
    MeasurementAnnotation,
    MeasurementItem,
    MeasurementKind,
    MEModel,
    MTypeClass,
    MTypeClassification,
    Simulation,
    SimulationCampaign,
    SingleNeuronSynaptome,
    Species,
    Strain,
    Subject,
    Usage,
)
from app.dependencies.common import FacetQueryParams
from app.filters.base import Aliases
from app.queries.types import ApplyOperations


def query_params_factory[I: Identifiable](
    db_model_class: Any, facet_keys: list[str], filter_keys: list[str], aliases: Aliases
) -> tuple[dict[str, FacetQueryParams], dict[str, ApplyOperations[I]]]:
    """Build and return query parameters.

    Args:
        db_model_class: The database model class.
        facet_keys: List of facet keys, used to build the dict of FacetQueryParams.
        filter_keys: List of filter keys, used to build the dict of ApplyOperations.
            The order of the keys is important to apply joins operations correctly and efficiently.
            In general, joins should be applied before left joins.
        aliases: Dict of aliases. It can be empty if aliases are not needed.

    Returns:
        Tuple with a dict of FacetQueryParams and a dict of ApplyOperations.
    """

    def _get_alias[T: type[Identifiable]](db_cls: T, name: str | None = None) -> T:
        value = aliases.get(db_cls, db_cls)
        # if multiple aliases for a db_cls e.g, {Agent: {"agent": alias1, "created_by": "alias2"}
        if isinstance(value, dict):
            # Fetch alias by name or assign db_cls if the alias is not passed as not needed
            value = db_cls if name is None else value.get(name, db_cls)
        return cast("T", value)

    morphology_alias = _get_alias(CellMorphology)
    cell_morphology_protocol_alias = _get_alias(CellMorphologyProtocol)
    emodel_alias = _get_alias(EModel)
    me_model_alias = _get_alias(MEModel)
    synaptome_alias = _get_alias(SingleNeuronSynaptome)
    subject_alias = _get_alias(Subject)
    agent_alias = _get_alias(Agent, "agent")
    contribution_alias = _get_alias(Agent, "contribution")
    created_by_alias = _get_alias(Agent, "created_by")
    updated_by_alias = _get_alias(Agent, "updated_by")
    pre_mtype_alias = _get_alias(MTypeClass, "pre_mtype")
    post_mtype_alias = _get_alias(MTypeClass, "post_mtype")
    brain_region_alias = _get_alias(BrainRegion, "brain_region")
    pre_region_alias = _get_alias(BrainRegion, "pre_region")
    post_region_alias = _get_alias(BrainRegion, "post_region")
    entity_alias = _get_alias(Entity)
    simulation_alias = _get_alias(Simulation)
    used_alias = _get_alias(Entity, "used")
    generated_alias = _get_alias(Entity, "generated")
    circuit_alias = _get_alias(Circuit)
    ion_channel_alias = _get_alias(IonChannel)
    em_dense_reconstruction_dataset_alias = _get_alias(EMDenseReconstructionDataset)
    ion_channel_model_alias = _get_alias(IonChannelModel, "ion_channel_model")
    ion_channel_modeling_config_alias = _get_alias(IonChannelModelingConfig)

    name_to_facet_query_params: dict[str, FacetQueryParams] = {
        "agent": {
            "id": agent_alias.id,
            "label": agent_alias.pref_label,
            "type": agent_alias.type,
        },
        "mtype": {"id": MTypeClass.id, "label": MTypeClass.pref_label},
        "etype": {"id": ETypeClass.id, "label": ETypeClass.pref_label},
        "species": {"id": Species.id, "label": Species.name},
        "strain": {"id": Strain.id, "label": Strain.name},
        "subject.species": {"id": Species.id, "label": Species.name},
        "subject.strain": {"id": Strain.id, "label": Strain.name},
        "contribution": {
            "id": contribution_alias.id,
            "label": contribution_alias.pref_label,
            "type": contribution_alias.type,
        },
        "brain_region": {"id": brain_region_alias.id, "label": brain_region_alias.name},
        "morphology": {"id": morphology_alias.id, "label": morphology_alias.name},
        "exemplar_morphology": {"id": morphology_alias.id, "label": morphology_alias.name},
        "cell_morphology_protocol": {
            "id": cell_morphology_protocol_alias.id,
            "label": cell_morphology_protocol_alias.generation_type,
        },
        "emodel": {"id": emodel_alias.id, "label": emodel_alias.name},
        "me_model": {"id": me_model_alias.id, "label": me_model_alias.name},
        "synaptome": {"id": synaptome_alias.id, "label": synaptome_alias.name},
        "created_by": {
            "id": created_by_alias.id,
            "label": created_by_alias.pref_label,
            "type": created_by_alias.type,
        },
        "updated_by": {
            "id": updated_by_alias.id,
            "label": updated_by_alias.pref_label,
            "type": updated_by_alias.type,
        },
        "pre_mtype": {"id": pre_mtype_alias.id, "label": pre_mtype_alias.pref_label},
        "post_mtype": {"id": post_mtype_alias.id, "label": post_mtype_alias.pref_label},
        "pre_region": {"id": pre_region_alias.id, "label": pre_region_alias.name},
        "post_region": {"id": post_region_alias.id, "label": post_region_alias.name},
        "simulation": {"id": simulation_alias.id, "label": simulation_alias.name},
        "simulation.circuit": {
            "id": circuit_alias.id,
            "label": circuit_alias.name,
        },
        "circuit": {"id": circuit_alias.id, "label": circuit_alias.name},
        "ion_channel": {"id": ion_channel_alias.id, "label": ion_channel_alias.label},
        "em_dense_reconstruction_dataset": {
            "id": em_dense_reconstruction_dataset_alias.id,
            "label": em_dense_reconstruction_dataset_alias.name,
        },
        "ion_channel_model": {
            "id": ion_channel_model_alias.id,
            "label": ion_channel_model_alias.name,
        },
        "ion_channel_modeling_config": {
            "id": ion_channel_modeling_config_alias.id,
            "label": ion_channel_modeling_config_alias.name,
        },
    }
    filter_joins = {
        "species": lambda q: q.join(Species, db_model_class.species_id == Species.id),
        "strain": lambda q: q.outerjoin(Strain, db_model_class.strain_id == Strain.id),
        "morphology": lambda q: q.join(
            morphology_alias, db_model_class.morphology_id == morphology_alias.id
        ),
        "exemplar_morphology": lambda q: q.join(
            morphology_alias, db_model_class.exemplar_morphology_id == morphology_alias.id
        ),
        "cell_morphology_protocol": lambda q: q.join(
            cell_morphology_protocol_alias,
            db_model_class.cell_morphology_protocol_id == cell_morphology_protocol_alias.id,
        ),
        "emodel": lambda q: q.join(emodel_alias, db_model_class.emodel_id == emodel_alias.id),
        "entity": lambda q: q.join(entity_alias, db_model_class.entity_id == entity_alias.id),
        "me_model": lambda q: q.join(
            me_model_alias, db_model_class.me_model_id == me_model_alias.id
        ),
        "synaptome": lambda q: q.join(
            synaptome_alias, db_model_class.synaptome_id == synaptome_alias.id
        ),
        "brain_region": lambda q: q.join(
            brain_region_alias, db_model_class.brain_region_id == brain_region_alias.id
        ),
        "agent": lambda q: q.join(Agent, db_model_class.agent_id == Agent.id),
        "contribution": lambda q: q.outerjoin(
            Contribution, db_model_class.id == Contribution.entity_id
        ).outerjoin(contribution_alias, Contribution.agent_id == contribution_alias.id),
        "mtype": lambda q: q.outerjoin(
            MTypeClassification, db_model_class.id == MTypeClassification.entity_id
        ).outerjoin(MTypeClass, MTypeClass.id == MTypeClassification.mtype_class_id),
        "etype": lambda q: q.outerjoin(
            ETypeClassification, db_model_class.id == ETypeClassification.entity_id
        ).outerjoin(ETypeClass, ETypeClass.id == ETypeClassification.etype_class_id),
        "created_by": lambda q: q.join(
            created_by_alias, db_model_class.created_by_id == created_by_alias.id
        ),
        "updated_by": lambda q: q.join(
            updated_by_alias, db_model_class.updated_by_id == updated_by_alias.id
        ),
        "subject": lambda q: q.outerjoin(
            subject_alias, db_model_class.subject_id == subject_alias.id
        ),
        "subject.species": lambda q: q.outerjoin(Species, subject_alias.species_id == Species.id),
        "subject.strain": lambda q: q.outerjoin(Strain, subject_alias.strain_id == Strain.id),
        "measurement_kind": lambda q: q.join(MeasurementKind),
        "measurement_kind.measurement_item": lambda q: q.join(MeasurementItem),
        "measurement_annotation": lambda q: q.outerjoin(
            MeasurementAnnotation, MeasurementAnnotation.entity_id == db_model_class.id
        ),
        "measurement_annotation.measurement_kind": lambda q: q.outerjoin(
            MeasurementKind,
            MeasurementKind.measurement_annotation_id == MeasurementAnnotation.id,
        ),
        "measurement_annotation.measurement_kind.measurement_item": lambda q: q.outerjoin(
            MeasurementItem, MeasurementItem.measurement_kind_id == MeasurementKind.id
        ),
        "pre_mtype": lambda q: q.join(
            pre_mtype_alias, db_model_class.pre_mtype_id == pre_mtype_alias.id
        ),
        "post_mtype": lambda q: q.join(
            post_mtype_alias, db_model_class.post_mtype_id == post_mtype_alias.id
        ),
        "pre_region": lambda q: q.join(
            pre_region_alias, db_model_class.pre_region_id == pre_region_alias.id
        ),
        "post_region": lambda q: q.join(
            post_region_alias, db_model_class.post_region_id == post_region_alias.id
        ),
        "simulation": lambda q: q.outerjoin(
            simulation_alias, db_model_class.id == simulation_alias.simulation_campaign_id
        ),
        "simulation.circuit": lambda q: q.join(
            circuit_alias, simulation_alias.entity_id == circuit_alias.id
        ),
        "circuit": lambda q: q.join(
            circuit_alias,
            (
                db_model_class.entity_id
                if db_model_class == SimulationCampaign
                else db_model_class.circuit_id
            )
            == circuit_alias.id,
        ),
        "used": lambda q: q.outerjoin(
            Usage, db_model_class.id == Usage.usage_activity_id
        ).outerjoin(used_alias, Usage.usage_entity_id == used_alias.id),
        "generated": lambda q: q.outerjoin(
            Generation, db_model_class.id == Generation.generation_activity_id
        ).outerjoin(generated_alias, Generation.generation_entity_id == generated_alias.id),
        "ion_channel": lambda q: q.join(
            ion_channel_alias, db_model_class.ion_channel_id == ion_channel_alias.id
        ),
        "em_dense_reconstruction_dataset": lambda q: q.join(
            em_dense_reconstruction_dataset_alias,
            em_dense_reconstruction_dataset_alias.id
            == db_model_class.em_dense_reconstruction_dataset_id,
        ),
        "ion_channel_model": lambda q: q.outerjoin(
            IonChannelModelToEModel,
            db_model_class.id == IonChannelModelToEModel.emodel_id,
        ).outerjoin(
            ion_channel_model_alias,
            IonChannelModelToEModel.ion_channel_model_id == ion_channel_model_alias.id,
        ),
        "ion_channel_modeling_config": lambda q: q.outerjoin(
            ion_channel_modeling_config_alias,
            db_model_class.id == ion_channel_modeling_config_alias.ion_channel_modeling_campaign_id,
        ),
    }
    name_to_facet_query_params = {k: name_to_facet_query_params[k] for k in facet_keys}
    filter_joins = {k: filter_joins[k] for k in filter_keys}
    return name_to_facet_query_params, filter_joins
