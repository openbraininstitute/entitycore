from typing import Any, cast

from app.db.model import (
    Agent,
    BrainRegion,
    Contribution,
    EModel,
    Entity,
    ETypeClass,
    ETypeClassification,
    Generation,
    Identifiable,
    MeasurementAnnotation,
    MeasurementItem,
    MeasurementKind,
    MEModel,
    MTypeClass,
    MTypeClassification,
    CellMorphology,
    Simulation,
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
    pre_region_alias = _get_alias(BrainRegion, "pre_region")
    post_region_alias = _get_alias(BrainRegion, "post_region")
    entity_alias = _get_alias(Entity)
    simulation_alias = _get_alias(Simulation)
    used_alias = _get_alias(Entity, "used")
    generated_alias = _get_alias(Entity, "generated")

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
        "brain_region": {"id": BrainRegion.id, "label": BrainRegion.name},
        "morphology": {"id": morphology_alias.id, "label": morphology_alias.name},
        "exemplar_morphology": {"id": morphology_alias.id, "label": morphology_alias.name},
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
        "emodel": lambda q: q.join(emodel_alias, db_model_class.emodel_id == emodel_alias.id),
        "entity": lambda q: q.join(entity_alias, db_model_class.entity_id == entity_alias.id),
        "me_model": lambda q: q.join(
            me_model_alias, db_model_class.me_model_id == me_model_alias.id
        ),
        "synaptome": lambda q: q.join(
            synaptome_alias, db_model_class.synaptome_id == synaptome_alias.id
        ),
        "brain_region": lambda q: q.join(
            BrainRegion, db_model_class.brain_region_id == BrainRegion.id
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
        "used": lambda q: q.outerjoin(
            Usage, db_model_class.id == Usage.usage_activity_id
        ).outerjoin(used_alias, Usage.usage_entity_id == used_alias.id),
        "generated": lambda q: q.outerjoin(
            Generation, db_model_class.id == Generation.generation_activity_id
        ).outerjoin(generated_alias, Generation.generation_entity_id == generated_alias.id),
    }
    name_to_facet_query_params = {k: name_to_facet_query_params[k] for k in facet_keys}
    filter_joins = {k: filter_joins[k] for k in filter_keys}
    return name_to_facet_query_params, filter_joins
