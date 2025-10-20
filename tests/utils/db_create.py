from tests.utils import add_db


def create_entity(
    db, entity_class, *, person_id, authorized_public, authorized_project_id, json_data
):
    return add_db(
        db,
        entity_class(
            **json_data
            | {
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_public": authorized_public,
                "authorized_project_id": authorized_project_id,
            }
        ),
    )
