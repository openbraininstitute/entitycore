from app.db.model import (
    Activity,
    EmCellMeshToSkeletonizationCampaign,
    EModel,
    EntityToTaskConfig,
    Generation,
    Identifiable,
    IonChannelModelingCampaign,
    IonChannelModelToEModel,
    IonChannelRecordingToIonChannelModelingCampaign,
    SkeletonizationCampaign,
    TaskConfig,
    Usage,
)
from app.queries.types import NestedRelationships

NESTED_RELATIONSHIPS_MAP: dict[type[Identifiable], NestedRelationships] = {
    Activity: {
        "used_ids": {
            "relationship_name": "used",
            "db_model_factory": lambda *, parent_id, child_id: Usage(
                usage_activity_id=parent_id, usage_entity_id=child_id
            ),
            "nested_id_getter": lambda *, items: items,  # used_ids is already the list of ids
        },
        "generated_ids": {
            "relationship_name": "generated",
            "db_model_factory": lambda *, parent_id, child_id: Generation(
                generation_activity_id=parent_id, generation_entity_id=child_id
            ),
            "nested_id_getter": lambda *, items: items,  # generated_ids is already the list of ids
        },
    },
    TaskConfig: {
        "inputs": {
            "relationship_name": "inputs",
            "db_model_factory": lambda *, parent_id, child_id: EntityToTaskConfig(
                task_config_id=parent_id,
                entity_id=child_id,
            ),
            "nested_id_getter": lambda *, items: [item.id for item in items],
        },
    },
    EModel: {
        "ion_channel_models": {
            "relationship_name": "ion_channel_models",
            "db_model_factory": lambda *, parent_id, child_id: IonChannelModelToEModel(
                emodel_id=parent_id,
                ion_channel_model_id=child_id,
            ),
            "nested_id_getter": lambda *, items: [item.id for item in items],
        },
    },
    IonChannelModelingCampaign: {
        "input_recordings": {
            "relationship_name": "input_recordings",
            "db_model_factory": lambda *, parent_id, child_id: (
                IonChannelRecordingToIonChannelModelingCampaign(
                    ion_channel_modeling_campaign_id=parent_id,
                    ion_channel_recording_id=child_id,
                )
            ),
            "nested_id_getter": lambda *, items: [item.id for item in items],
        },
    },
    SkeletonizationCampaign: {
        "input_meshes": {
            "relationship_name": "input_meshes",
            "db_model_factory": lambda *, parent_id, child_id: EmCellMeshToSkeletonizationCampaign(
                skeletonization_campaign_id=parent_id,
                em_cell_mesh_id=child_id,
            ),
            "nested_id_getter": lambda *, items: [item.id for item in items],
        },
    },
}
