import uuid

from fastapi import HTTPException

from app.logger import L


def ensure_readable(entity, project_id: uuid.UUID | None) -> None:
    if not (
        entity.authorized_public or (project_id and entity.authorized_project_id == project_id)
    ):
        L.warning("Attempting to create an annotation for an entity inaccessible to user")
        raise HTTPException(
            status_code=404,
            detail=f"Cannot access entity {entity.id}",
        )
