import functools
from itertools import chain
from types import MappingProxyType
from typing import Any, NamedTuple

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase

from app.db.model import (
    Agent,
    BrainRegion,
    CellMorphology,
    CellMorphologyProtocol,
    Circuit,
    Contribution,
    Derivation,
    EMCellMesh,
    EMDenseReconstructionDataset,
    EModel,
    Entity,
    ETypeClass,
    ETypeClassification,
    Generation,
    IonChannel,
    IonChannelModel,
    IonChannelModelingConfig,
    IonChannelModelToEModel,
    Measurement,
    MeasurementAnnotation,
    MeasurementItem,
    MeasurementKind,
    MeasurementLabel,
    MEModel,
    MTypeClass,
    MTypeClassification,
    PlatformUser,
    Simulation,
    SingleNeuronSynaptome,
    SkeletonizationConfig,
    Species,
    Strain,
    Subject,
    TaskConfig,
    Usage,
    ValidationResult,
)
from app.db.types import MeasurementStatistic
from app.queries.alias_registry import Aliases, get_alias
from app.queries.types import (
    FacetQueryParams,
    FacetQueryParamsMap,
    JoinSpec,
    JoinSpecMap,
)
from app.queries.utils import expand_dotted_key
from app.utils.uuid import value_to_uuid


class _Spec(NamedTuple):
    facet: FacetQueryParams | None
    join: JoinSpec


class _SpecRegistry:
    """Registry of spec_* methods, each returning a _Spec (facet + join) for a filter/facet key."""

    def __init__(self, db_model_class: Any) -> None:
        self._m = db_model_class
        self._collected_aliases: dict[type[DeclarativeBase], dict[str, Any]] = {}

    def _a[T: type[DeclarativeBase]](self, db_cls: T, name: str) -> T:
        """Return or retrieve a cached named alias for db_cls.

        The name MUST match the key that CustomFilter.filter()/sort() will use to look up
        this alias. For top-level specs this is the filter field name (e.g. "me_model").
        For nested specs accessed through a parent, it's the dot-qualified path
        (e.g. "synaptome.me_model") so that path-aware resolution finds it.
        """
        alias = get_alias(db_cls, name)
        self._collected_aliases.setdefault(db_cls, {})[name] = alias
        return alias

    def collected_aliases(self) -> Aliases:
        """Return the Aliases mapping from all aliases collected during spec resolution."""
        return MappingProxyType(
            {k: MappingProxyType(v) for k, v in self._collected_aliases.items()}
        )

    def spec_species(self) -> _Spec:
        m = self._m
        return _Spec(
            facet={"id": Species.id, "label": Species.name},
            join=JoinSpec(join=lambda q: q.join(Species, m.species_id == Species.id)),
        )

    def spec_strain(self) -> _Spec:
        m = self._m
        return _Spec(
            facet={"id": Strain.id, "label": Strain.name},
            join=JoinSpec(
                join=lambda q: q.outerjoin(Strain, m.strain_id == Strain.id),
                filter_join=lambda q: q.join(Strain, m.strain_id == Strain.id),
            ),
        )

    def spec_mtype(self) -> _Spec:
        m = self._m
        return _Spec(
            facet={"id": MTypeClass.id, "label": MTypeClass.pref_label},
            join=JoinSpec(
                join=lambda q: q.outerjoin(
                    MTypeClassification, m.id == MTypeClassification.entity_id
                ).outerjoin(MTypeClass, MTypeClass.id == MTypeClassification.mtype_class_id),
                filter_join=lambda q: q.join(
                    MTypeClassification, m.id == MTypeClassification.entity_id
                ).join(MTypeClass, MTypeClass.id == MTypeClassification.mtype_class_id),
            ),
        )

    def spec_etype(self) -> _Spec:
        m = self._m
        return _Spec(
            facet={"id": ETypeClass.id, "label": ETypeClass.pref_label},
            join=JoinSpec(
                join=lambda q: q.outerjoin(
                    ETypeClassification, m.id == ETypeClassification.entity_id
                ).outerjoin(ETypeClass, ETypeClass.id == ETypeClassification.etype_class_id),
                filter_join=lambda q: q.join(
                    ETypeClassification, m.id == ETypeClassification.entity_id
                ).join(ETypeClass, ETypeClass.id == ETypeClassification.etype_class_id),
            ),
        )

    def spec_subject(self) -> _Spec:
        a = self._a(Subject, "subject")
        return _Spec(
            facet={"id": a.id, "label": a.name},
            join=JoinSpec(
                join=lambda q: q.outerjoin(a, self._m.subject_id == a.id),
                filter_join=lambda q: q.join(a, self._m.subject_id == a.id),
            ),
        )

    def spec_subject__species(self) -> _Spec:
        a = self._a(Subject, "subject")
        return _Spec(
            facet={"id": Species.id, "label": Species.name},
            join=JoinSpec(
                join=lambda q: q.outerjoin(Species, a.species_id == Species.id),
                filter_join=lambda q: q.join(Species, a.species_id == Species.id),
            ),
        )

    def spec_subject__strain(self) -> _Spec:
        a = self._a(Subject, "subject")
        return _Spec(
            facet={"id": Strain.id, "label": Strain.name},
            join=JoinSpec(
                join=lambda q: q.outerjoin(Strain, a.strain_id == Strain.id),
                filter_join=lambda q: q.join(Strain, a.strain_id == Strain.id),
            ),
        )

    @staticmethod
    def spec_release_version() -> _Spec:
        facet_id = value_to_uuid(prefix="release_version", value=EMCellMesh.release_version)
        facet_label = sa.cast(EMCellMesh.release_version, sa.String)
        return _Spec(facet={"id": facet_id, "label": facet_label}, join=JoinSpec(join=lambda q: q))

    def spec_morphology(self) -> _Spec:
        a = self._a(CellMorphology, "morphology")
        return _Spec(
            facet={"id": a.id, "label": a.name},
            join=JoinSpec(join=lambda q: q.join(a, self._m.morphology_id == a.id)),
        )

    def spec_exemplar_morphology(self) -> _Spec:
        a = self._a(CellMorphology, "exemplar_morphology")
        return _Spec(
            facet={"id": a.id, "label": a.name},
            join=JoinSpec(join=lambda q: q.join(a, self._m.exemplar_morphology_id == a.id)),
        )

    def spec_cell_morphology_protocol(self) -> _Spec:
        a = self._a(CellMorphologyProtocol, "cell_morphology_protocol")
        return _Spec(
            facet={"id": a.id, "label": a.generation_type},
            join=JoinSpec(join=lambda q: q.join(a, self._m.cell_morphology_protocol_id == a.id)),
        )

    def spec_emodel(self) -> _Spec:
        a = self._a(EModel, "emodel")
        return _Spec(
            facet={"id": a.id, "label": a.name},
            join=JoinSpec(join=lambda q: q.join(a, self._m.emodel_id == a.id)),
        )

    def spec_me_model(self) -> _Spec:
        a = self._a(MEModel, "me_model")
        return _Spec(
            facet={"id": a.id, "label": a.name},
            join=JoinSpec(join=lambda q: q.join(a, self._m.me_model_id == a.id)),
        )

    def spec_me_model__etype(self) -> _Spec:
        me = self._a(MEModel, "me_model")
        return _Spec(
            facet={"id": ETypeClass.id, "label": ETypeClass.pref_label},
            join=JoinSpec(
                join=lambda q: q.join(
                    ETypeClassification, ETypeClassification.entity_id == me.id
                ).join(ETypeClass, ETypeClass.id == ETypeClassification.etype_class_id),
            ),
        )

    def spec_me_model__mtype(self) -> _Spec:
        me = self._a(MEModel, "me_model")
        return _Spec(
            facet={"id": MTypeClass.id, "label": MTypeClass.pref_label},
            join=JoinSpec(
                join=lambda q: q.join(
                    MTypeClassification, MTypeClassification.entity_id == me.id
                ).join(MTypeClass, MTypeClass.id == MTypeClassification.mtype_class_id),
            ),
        )

    def spec_me_model__species(self) -> _Spec:
        me = self._a(MEModel, "me_model")
        return _Spec(
            facet=None,
            join=JoinSpec(join=lambda q: q.join(Species, me.species_id == Species.id)),
        )

    def spec_synaptome(self) -> _Spec:
        a = self._a(SingleNeuronSynaptome, "synaptome")
        return _Spec(
            facet={"id": a.id, "label": a.name},
            join=JoinSpec(join=lambda q: q.join(a, self._m.synaptome_id == a.id)),
        )

    def spec_synaptome__me_model(self) -> _Spec:
        synaptome = self._a(SingleNeuronSynaptome, "synaptome")
        me = self._a(MEModel, "synaptome.me_model")
        return _Spec(
            facet=None, join=JoinSpec(join=lambda q: q.join(me, me.id == synaptome.me_model_id))
        )

    def spec_synaptome__me_model__species(self) -> _Spec:
        me = self._a(MEModel, "synaptome.me_model")
        return _Spec(
            facet=None, join=JoinSpec(join=lambda q: q.join(Species, Species.id == me.species_id))
        )

    def spec_agent(self) -> _Spec:
        a = self._a(Agent, "agent")
        return _Spec(
            facet={"id": a.id, "label": a.pref_label, "type": a.type},
            join=JoinSpec(join=lambda q: q.join(a, self._m.agent_id == a.id)),
        )

    def spec_contribution(self) -> _Spec:
        a = self._a(Agent, "contribution")
        return _Spec(
            facet={"id": a.id, "label": a.pref_label, "type": a.type},
            join=JoinSpec(
                join=lambda q: q.outerjoin(
                    Contribution, self._m.id == Contribution.entity_id
                ).outerjoin(a, Contribution.agent_id == a.id),
                filter_join=lambda q: q.join(
                    Contribution, self._m.id == Contribution.entity_id
                ).join(a, Contribution.agent_id == a.id),
            ),
        )

    def spec_created_by(self) -> _Spec:
        a = self._a(PlatformUser, "created_by")
        return _Spec(
            facet={"id": a.id, "label": a.pref_label},
            join=JoinSpec(join=lambda q: q.join(a, self._m.created_by_id == a.id)),
        )

    def spec_updated_by(self) -> _Spec:
        a = self._a(PlatformUser, "updated_by")
        return _Spec(
            facet={"id": a.id, "label": a.pref_label},
            join=JoinSpec(join=lambda q: q.join(a, self._m.updated_by_id == a.id)),
        )

    def spec_pre_mtype(self) -> _Spec:
        a = self._a(MTypeClass, "pre_mtype")
        return _Spec(
            facet={"id": a.id, "label": a.pref_label},
            join=JoinSpec(join=lambda q: q.join(a, self._m.pre_mtype_id == a.id)),
        )

    def spec_post_mtype(self) -> _Spec:
        a = self._a(MTypeClass, "post_mtype")
        return _Spec(
            facet={"id": a.id, "label": a.pref_label},
            join=JoinSpec(join=lambda q: q.join(a, self._m.post_mtype_id == a.id)),
        )

    def spec_brain_region(self) -> _Spec:
        br = self._a(BrainRegion, "brain_region")
        return _Spec(
            facet={"id": br.id, "label": br.name},
            join=JoinSpec(
                join=lambda q: q.join(br, self._m.brain_region_id == br.id),
            ),
        )

    def spec_pre_region(self) -> _Spec:
        a = self._a(BrainRegion, "pre_region")
        return _Spec(
            facet={"id": a.id, "label": a.name},
            join=JoinSpec(join=lambda q: q.join(a, self._m.pre_region_id == a.id)),
        )

    def spec_post_region(self) -> _Spec:
        a = self._a(BrainRegion, "post_region")
        return _Spec(
            facet={"id": a.id, "label": a.name},
            join=JoinSpec(join=lambda q: q.join(a, self._m.post_region_id == a.id)),
        )

    def spec_simulation(self) -> _Spec:
        a = self._a(Simulation, "simulation")
        return _Spec(
            facet={"id": a.id, "label": a.name},
            join=JoinSpec(
                join=lambda q: q.outerjoin(a, self._m.id == a.simulation_campaign_id),
                filter_join=lambda q: q.join(a, self._m.id == a.simulation_campaign_id),
            ),
        )

    def spec_circuit(self) -> _Spec:
        a = self._a(Circuit, "circuit")
        m = self._m
        fk = m.circuit_id if hasattr(m, "circuit_id") else m.entity_id
        return _Spec(
            facet={"id": a.id, "label": a.name},
            join=JoinSpec(join=lambda q: q.join(a, fk == a.id)),
        )

    def spec_em_dense_reconstruction_dataset(self) -> _Spec:
        a = self._a(EMDenseReconstructionDataset, "em_dense_reconstruction_dataset")
        return _Spec(
            facet={"id": a.id, "label": a.name},
            join=JoinSpec(
                join=lambda q: q.join(a, a.id == self._m.em_dense_reconstruction_dataset_id)
            ),
        )

    def spec_ion_channel(self) -> _Spec:
        a = self._a(IonChannel, "ion_channel")
        return _Spec(
            facet={"id": a.id, "label": a.label},
            join=JoinSpec(join=lambda q: q.join(a, self._m.ion_channel_id == a.id)),
        )

    def spec_ion_channel_model(self) -> _Spec:
        a = self._a(IonChannelModel, "ion_channel_model")
        return _Spec(
            facet={"id": a.id, "label": a.name},
            join=JoinSpec(
                join=lambda q: q.outerjoin(
                    IonChannelModelToEModel, self._m.id == IonChannelModelToEModel.emodel_id
                ).outerjoin(a, IonChannelModelToEModel.ion_channel_model_id == a.id),
                filter_join=lambda q: q.join(
                    IonChannelModelToEModel, self._m.id == IonChannelModelToEModel.emodel_id
                ).join(a, IonChannelModelToEModel.ion_channel_model_id == a.id),
            ),
        )

    def spec_ion_channel_modeling_config(self) -> _Spec:
        a = self._a(IonChannelModelingConfig, "ion_channel_modeling_config")
        return _Spec(
            facet={"id": a.id, "label": a.name},
            join=JoinSpec(
                join=lambda q: q.join(a, self._m.id == a.ion_channel_modeling_campaign_id)
            ),
        )

    def spec_skeletonization_config(self) -> _Spec:
        a = self._a(SkeletonizationConfig, "skeletonization_config")
        return _Spec(
            facet={"id": a.id, "label": a.name},
            join=JoinSpec(join=lambda q: q.join(a, self._m.id == a.skeletonization_campaign_id)),
        )

    def spec_task_config_generator(self) -> _Spec:
        a = self._a(TaskConfig, "task_config_generator")
        return _Spec(
            facet={"id": a.id, "label": a.name},
            join=JoinSpec(
                join=lambda q: q.outerjoin(a, self._m.task_config_generator_id == a.id),
                filter_join=lambda q: q.join(a, self._m.task_config_generator_id == a.id),
            ),
        )

    def spec_validation_result(self) -> _Spec:
        a = self._a(ValidationResult, "validation_result")
        return _Spec(
            facet={"id": a.id, "label": a.name},
            join=JoinSpec(
                join=lambda q: q.outerjoin(a, self._m.id == a.validated_entity_id),
                filter_join=lambda q: q.join(a, self._m.id == a.validated_entity_id),
            ),
        )

    def spec_measurement_mean(self) -> _Spec:
        a = self._a(Measurement, "measurement_mean")
        cond = (self._m.id == a.entity_id) & (a.name == MeasurementStatistic.mean)
        return _Spec(
            facet=None,
            join=JoinSpec(
                join=lambda q: q.outerjoin(a, cond),
                filter_join=lambda q: q.join(a, cond),
            ),
        )

    def spec_measurement_standard_error(self) -> _Spec:
        a = self._a(Measurement, "measurement_standard_error")
        cond = (self._m.id == a.entity_id) & (a.name == MeasurementStatistic.standard_error)
        return _Spec(
            facet=None,
            join=JoinSpec(
                join=lambda q: q.outerjoin(a, cond),
                filter_join=lambda q: q.join(a, cond),
            ),
        )

    def spec_measurement_sample_size(self) -> _Spec:
        a = self._a(Measurement, "measurement_sample_size")
        cond = (self._m.id == a.entity_id) & (a.name == MeasurementStatistic.sample_size)
        return _Spec(
            facet=None,
            join=JoinSpec(
                join=lambda q: q.outerjoin(a, cond),
                filter_join=lambda q: q.join(a, cond),
            ),
        )

    def spec_entity(self) -> _Spec:
        a = self._a(Entity, "entity")
        return _Spec(facet=None, join=JoinSpec(join=lambda q: q.join(a, self._m.entity_id == a.id)))

    @staticmethod
    def spec_measurement_kind() -> _Spec:
        return _Spec(facet=None, join=JoinSpec(join=lambda q: q.join(MeasurementKind)))

    @staticmethod
    def spec_measurement_kind__measurement_item() -> _Spec:
        return _Spec(facet=None, join=JoinSpec(join=lambda q: q.join(MeasurementItem)))

    @staticmethod
    def spec_measurement_kind__pref_label() -> _Spec:
        return _Spec(facet=None, join=JoinSpec(join=lambda q: q.join(MeasurementLabel)))

    def spec_measurement_annotation(self) -> _Spec:
        m = self._m
        return _Spec(
            facet=None,
            join=JoinSpec(
                join=lambda q: q.outerjoin(
                    MeasurementAnnotation, MeasurementAnnotation.entity_id == m.id
                ),
                filter_join=lambda q: q.join(
                    MeasurementAnnotation, MeasurementAnnotation.entity_id == m.id
                ),
            ),
        )

    @staticmethod
    def spec_measurement_annotation__measurement_kind() -> _Spec:
        return _Spec(
            facet=None,
            join=JoinSpec(
                join=lambda q: q.outerjoin(
                    MeasurementKind,
                    MeasurementKind.measurement_annotation_id == MeasurementAnnotation.id,
                ),
                filter_join=lambda q: q.join(
                    MeasurementKind,
                    MeasurementKind.measurement_annotation_id == MeasurementAnnotation.id,
                ),
            ),
        )

    @staticmethod
    def spec_measurement_annotation__measurement_kind__measurement_item() -> _Spec:
        return _Spec(
            facet=None,
            join=JoinSpec(
                join=lambda q: q.outerjoin(
                    MeasurementItem, MeasurementItem.measurement_kind_id == MeasurementKind.id
                ),
                filter_join=lambda q: q.join(
                    MeasurementItem, MeasurementItem.measurement_kind_id == MeasurementKind.id
                ),
            ),
        )

    @staticmethod
    def spec_measurement_annotation__measurement_kind__pref_label() -> _Spec:
        return _Spec(
            facet=None,
            join=JoinSpec(
                join=lambda q: q.outerjoin(
                    MeasurementLabel, MeasurementLabel.id == MeasurementKind.measurement_label_id
                ),
                filter_join=lambda q: q.join(
                    MeasurementLabel, MeasurementLabel.id == MeasurementKind.measurement_label_id
                ),
            ),
        )

    def spec_generated_derivation(self) -> _Spec:
        a = self._a(Derivation, "generated_derivation")
        return _Spec(
            facet=None,
            join=JoinSpec(
                join=lambda q: q.outerjoin(a, self._m.id == a.generated_id),
                filter_join=lambda q: q.join(a, self._m.id == a.generated_id),
            ),
        )

    def spec_used_derivation(self) -> _Spec:
        a = self._a(Derivation, "used_derivation")
        return _Spec(
            facet=None,
            join=JoinSpec(
                join=lambda q: q.outerjoin(a, self._m.id == a.used_id),
                filter_join=lambda q: q.join(a, self._m.id == a.used_id),
            ),
        )

    def spec_used(self) -> _Spec:
        a = self._a(Entity, "used")
        return _Spec(
            facet=None,
            join=JoinSpec(
                join=lambda q: q.outerjoin(Usage, self._m.id == Usage.usage_activity_id).outerjoin(
                    a, Usage.usage_entity_id == a.id
                ),
                filter_join=lambda q: q.join(Usage, self._m.id == Usage.usage_activity_id).join(
                    a, Usage.usage_entity_id == a.id
                ),
            ),
        )

    def spec_generated(self) -> _Spec:
        a = self._a(Entity, "generated")
        return _Spec(
            facet=None,
            join=JoinSpec(
                join=lambda q: q.outerjoin(
                    Generation, self._m.id == Generation.generation_activity_id
                ).outerjoin(a, Generation.generation_entity_id == a.id),
                filter_join=lambda q: q.join(
                    Generation, self._m.id == Generation.generation_activity_id
                ).join(a, Generation.generation_entity_id == a.id),
            ),
        )

    def resolve(self, key: str) -> _Spec:
        method_name = "spec_" + key.replace(".", "__")
        method = getattr(self, method_name, None)
        if method is None:
            msg = f"Unknown key: {key!r}"
            raise ValueError(msg)
        return method()


def _expand_filter_keys(filter_keys: tuple[str, ...]) -> tuple[str, ...]:
    """Ensure parent keys are present for every dot-separated child key.

    Examples:
        ("subject.species", "brain_region") -> ("subject", "subject.species", "brain_region")
        ("subject", "subject.species") -> ("subject", "subject.species")  (no change)
    """
    return tuple(dict.fromkeys(chain.from_iterable(expand_dotted_key(k) for k in filter_keys)))


def _is_entity_model(db_model_class: type[DeclarativeBase]) -> bool:
    return isinstance(db_model_class, type) and issubclass(db_model_class, Entity)


def _ensure_facet(facet: FacetQueryParams | None, key: str) -> FacetQueryParams:
    if facet is None:
        msg = f"Key {key!r} has no facet"
        raise ValueError(msg)
    return facet


@functools.cache
def _query_params_factory_cached(
    db_model_class: type[DeclarativeBase],
    facet_keys: tuple[str, ...],
    filter_keys: tuple[str, ...],
) -> tuple[
    FacetQueryParamsMap,
    JoinSpecMap,
    Aliases,
]:
    filter_keys = _expand_filter_keys(filter_keys)

    if facet_keys_not_in_filter := set(facet_keys) - set(filter_keys):
        msg = f"Facet keys missing from filter_keys: {facet_keys_not_in_filter}"
        raise ValueError(msg)

    if _is_entity_model(db_model_class):
        derivation_keys = ["generated_derivation", "used_derivation"]
        filter_keys = (
            *filter_keys,
            *(k for k in derivation_keys if k not in filter_keys),
        )

    registry = _SpecRegistry(db_model_class)
    resolved: dict[str, _Spec] = {k: registry.resolve(k) for k in filter_keys}
    facet_params = {k: _ensure_facet(resolved[k].facet, k) for k in facet_keys}
    join_specs = {k: resolved[k].join for k in filter_keys}
    return (
        facet_params,
        join_specs,
        registry.collected_aliases(),
    )


def query_params_factory(
    db_model_class: type[DeclarativeBase],
    facet_keys: list[str],
    filter_keys: list[str],
) -> tuple[
    FacetQueryParamsMap,
    JoinSpecMap,
    Aliases,
]:
    """Build and return query parameters.

    Args:
        db_model_class: The database model class.
        facet_keys: List of facet keys, used to build the dict of FacetQueryParams.
            Each facet key must also appear in filter_keys.
        filter_keys: List of JoinSpec keys. Order matters: joins are applied in this order,
            so inner joins should precede outer joins.
            Keys use dot-separated notation matching nested filter field names.

    Returns:
        Tuple of:
        - dict of FacetQueryParams keyed by facet_keys
        - dict of JoinSpec keyed by filter_keys (plus derivation keys for entity models)
        - Aliases mapping for use in filter/sort calls
    """
    return _query_params_factory_cached(
        db_model_class=db_model_class,
        facet_keys=tuple(facet_keys),
        filter_keys=tuple(filter_keys),
    )
