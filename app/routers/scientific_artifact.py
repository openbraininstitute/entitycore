# app/routers/scientific_artifact.py
import uuid
from app.schemas.scientific_artifact import ScientificArtifactRead


from fastapi import APIRouter, Depends
from app.dependencies.auth import UserContextWithProjectIdDep
from app.dependencies.db import SessionDep
from app.queries.common import router_create_one, router_read_one
from app.schemas.scientific_artifact import ScientificArtifactMixin
from app.db.model import ScientificArtifact

router = APIRouter()

@router.post("/scientific-artifacts", response_model=ScientificArtifactMixin)
def create_scientific_artifact(
    artifact: ScientificArtifactMixin,
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
):
    return router_create_one(
        db=db,
        db_model_class=ScientificArtifact,
        authorized_project_id=user_context.project_id,
        json_model=artifact,
        response_schema_class=ScientificArtifactMixin,
    )

@router.get("/scientific-artifacts/{id_}", response_model=ScientificArtifactMixin)
def read_scientific_artifact(
    id_: uuid.UUID,
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
):
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=ScientificArtifact,
        authorized_project_id=user_context.project_id,
        response_schema_class=ScientificArtifactMixin,
        apply_operations=None,
    )

@router.get("/scientific-artifacts/{id_}", response_model=ScientificArtifactRead)
def read_scientific_artifact(id_: uuid.UUID, db: SessionDep):
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=ScientificArtifact,
        response_schema_class=ScientificArtifactRead,
    )