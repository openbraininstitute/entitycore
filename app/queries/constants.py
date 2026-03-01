from app.db.model import Generation, TaskConfigToEntity, Usage
from app.queries.types import NestedRelationships

NESTED_ACTIVITY_RELATIONSHIPS: NestedRelationships = {
    "used_ids": {
        "relationship_name": "used",
        "db_model_factory": lambda *, left_id, right_id: Usage(
            usage_activity_id=left_id, usage_entity_id=right_id
        ),
    },
    "generated_ids": {
        "relationship_name": "generated",
        "db_model_factory": lambda *, left_id, right_id: Generation(
            generation_activity_id=left_id, generation_entity_id=right_id
        ),
    },
}

NESTED_TASK_CONFIG_RELATIONSHIPS: NestedRelationships = {
    "input_ids": {
        "relationship_name": "input",
        "db_model_factory": lambda *, left_id, right_id: TaskConfigToEntity(
            task_config_id=left_id, entity_id=right_id
        ),
    },
}
