from app.db.model import CampaignToEntity, Generation, TaskConfigToEntity, Usage
from app.queries.types import NestedRelationships, UpdateRelationshipPolicy

NESTED_ACTIVITY_RELATIONSHIPS: NestedRelationships = {
    "used_ids": {
        "relationship_name": "used",
        "db_model_factory": lambda *, left_id, right_id: Usage(
            usage_activity_id=left_id, usage_entity_id=right_id
        ),
        # used_ids should be set only on creation
        "update_policy": UpdateRelationshipPolicy.never,
    },
    "generated_ids": {
        "relationship_name": "generated",
        "db_model_factory": lambda *, left_id, right_id: Generation(
            generation_activity_id=left_id, generation_entity_id=right_id
        ),
        # generated_ids can be set on creation, or updated once if empty
        "update_policy": UpdateRelationshipPolicy.if_empty,
    },
}

NESTED_CAMPAIGN_RELATIONSHIPS: NestedRelationships = {
    "inputs_ids": {
        "relationship_name": "inputs",
        "db_model_factory": lambda *, left_id, right_id: CampaignToEntity(
            campaign_id=left_id, entity_id=right_id
        ),
        # input_ids can be set on creation, or updated once if empty
        "update_policy": UpdateRelationshipPolicy.if_empty,
    },
}

NESTED_TASK_CONFIG_RELATIONSHIPS: NestedRelationships = {
    "inputs_ids": {
        "relationship_name": "inputs",
        "db_model_factory": lambda *, left_id, right_id: TaskConfigToEntity(
            task_config_id=left_id, entity_id=right_id
        ),
        # input_ids can be set on creation, or updated once if empty
        "update_policy": UpdateRelationshipPolicy.if_empty,
    },
}
