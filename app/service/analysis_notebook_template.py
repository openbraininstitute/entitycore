import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING, cast

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.config import storages
from app.db.model import (
    Agent,
    AnalysisNotebookTemplate,
    Contribution,
    PlatformUser,
)
from app.db.types import EntityType, StorageType
from app.dependencies.auth import AdminContextDep, UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import ExpandDep, FacetsDep, PaginationQuery, SearchDep
from app.dependencies.db import RepoGroupDep, SessionDep
from app.dependencies.s3 import StorageClientFactoryDep
from app.errors import ApiError, ApiErrorCode
from app.filters.analysis_notebook_template import AnalysisNotebookTemplateFilterDep
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
    router_user_delete_one,
)
from app.queries.expand import EntityExpand
from app.queries.factory import query_params_factory
from app.queries.utils import get_or_create_user, is_user_authorized_for_clone
from app.schemas.analysis_notebook_template import (
    AnalysisNotebookTemplateAdminUpdate,
    AnalysisNotebookTemplateCreate,
    AnalysisNotebookTemplateRead,
    AnalysisNotebookTemplateUpdate,
    NotebookCloneRequest,
    NotebookCloneResponse,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse
from app.service import entity as entity_service
from app.service.asset import create_entity_asset_unverified, delete_asset_unverified
from app.utils.s3 import build_s3_path, copy_file
from app.utils.virtual_lab import resolve_virtual_lab_id

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(AnalysisNotebookTemplate.created_by),
        joinedload(AnalysisNotebookTemplate.updated_by),
        selectinload(AnalysisNotebookTemplate.assets),
        selectinload(AnalysisNotebookTemplate.contributions).joinedload(Contribution.agent),
        selectinload(AnalysisNotebookTemplate.contributions).joinedload(Contribution.role),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    expand: ExpandDep = None,
) -> AnalysisNotebookTemplateRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=AnalysisNotebookTemplate,
        user_context=user_context,
        response_schema_class=AnalysisNotebookTemplateRead,
        apply_operations=_load,
        expand=expand,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
    expand: ExpandDep = None,
) -> AnalysisNotebookTemplateRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=AnalysisNotebookTemplate,
        user_context=None,
        response_schema_class=AnalysisNotebookTemplateRead,
        apply_operations=_load,
        expand=expand,
    )


def create_one(
    db: SessionDep,
    json_model: AnalysisNotebookTemplateCreate,
    user_context: UserContextWithProjectIdDep,
) -> AnalysisNotebookTemplateRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=AnalysisNotebookTemplate,
        response_schema_class=AnalysisNotebookTemplateRead,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: AnalysisNotebookTemplateUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> AnalysisNotebookTemplateRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=AnalysisNotebookTemplate,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=AnalysisNotebookTemplateRead,
        apply_operations=_load,
        check_authorized_project=True,
    )


def admin_update_one(
    user_context: AdminContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: AnalysisNotebookTemplateAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> AnalysisNotebookTemplateRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=AnalysisNotebookTemplate,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=AnalysisNotebookTemplateRead,
        apply_operations=_load,
        check_authorized_project=False,
    )


def _read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: AnalysisNotebookTemplateFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    expand: set[EntityExpand] | None,
    check_authorized_project: bool,
) -> ListResponse[AnalysisNotebookTemplateRead]:
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(PlatformUser, flat=True)
    updated_by_alias = aliased(PlatformUser, flat=True)

    aliases: Aliases = {
        Agent: {
            "contribution": agent_alias,
        },
        PlatformUser: {
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
    }
    facet_keys = filter_keys = [
        "created_by",
        "updated_by",
        "contribution",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=AnalysisNotebookTemplate,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=AnalysisNotebookTemplate,
        with_search=with_search,
        with_in_brain_region=None,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=AnalysisNotebookTemplateRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
        check_authorized_project=check_authorized_project,
        expand=expand,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: AnalysisNotebookTemplateFilterDep,
    with_search: SearchDep,
    with_facets: FacetsDep,
    expand: ExpandDep = None,
) -> ListResponse[AnalysisNotebookTemplateRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=with_search,
        facets=with_facets,
        expand=expand,
        check_authorized_project=True,
    )


def admin_read_many(
    user_context: AdminContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: AnalysisNotebookTemplateFilterDep,
    with_search: SearchDep,
    with_facets: FacetsDep,
    expand: ExpandDep = None,
) -> ListResponse[AnalysisNotebookTemplateRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=with_search,
        facets=with_facets,
        expand=expand,
        check_authorized_project=False,
    )


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    return router_user_delete_one(
        id_=id_,
        db=db,
        db_model_class=AnalysisNotebookTemplate,
        user_context=user_context,
    )


def clone(
    user_context: UserContextDep,
    repos: RepoGroupDep,
    storage_client_factory: StorageClientFactoryDep,
    id_: uuid.UUID,
    json_model: NotebookCloneRequest,
) -> NotebookCloneResponse:
    notebook = cast(
        "AnalysisNotebookTemplate",
        entity_service.get_writable_entity_by_context(
            repos=repos,
            user_context=user_context,
            entity_type=EntityType.analysis_notebook_template,
            entity_id=id_,
        ),
    )

    if notebook.authorized_public:
        raise ApiError(
            message="Source notebook must be private",
            error_code=ApiErrorCode.ENTITY_FORBIDDEN,
            http_status_code=HTTPStatus.FORBIDDEN,
        )

    if notebook.authorized_project_id in json_model.target_project_ids:
        raise ApiError(
            message="Source project cannot be a target project",
            error_code=ApiErrorCode.ENTITY_FORBIDDEN,
            http_status_code=HTTPStatus.FORBIDDEN,
        )

    if not is_user_authorized_for_clone(
        user_context=user_context,
        target_project_ids=json_model.target_project_ids,
    ):
        raise ApiError(
            message="User is not admin of all required projects",
            error_code=ApiErrorCode.ENTITY_FORBIDDEN,
            http_status_code=HTTPStatus.FORBIDDEN,
        )

    public_conflict = (
        repos.db.execute(
            sa.select(AnalysisNotebookTemplate).where(
                AnalysisNotebookTemplate.name == notebook.name,
                AnalysisNotebookTemplate.authorized_project_id.in_(json_model.target_project_ids),
                AnalysisNotebookTemplate.authorized_public.is_(True),
            )
        )
        .scalars()
        .first()
    )

    if public_conflict:
        raise ApiError(
            message="A public notebook with the same name already exists in the target project",
            error_code=ApiErrorCode.ENTITY_FORBIDDEN,
            http_status_code=HTTPStatus.FORBIDDEN,
        )

    db_user = get_or_create_user(repos.db, user_profile=user_context.profile)
    created = []

    for project_id in json_model.target_project_ids:
        existing = repos.db.execute(
            sa.select(AnalysisNotebookTemplate).where(
                AnalysisNotebookTemplate.name == notebook.name,
                AnalysisNotebookTemplate.authorized_project_id == project_id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.description = notebook.description
            existing.scale = notebook.scale
            existing.specifications = notebook.specifications
            existing.assignment_id = notebook.assignment_id
            existing.updated_by_id = db_user.id
            repos.db.flush()
            repos.db.refresh(existing, ["assets"])

            for asset in list(existing.assets):
                delete_asset_unverified(
                    repos,
                    entity_type=EntityType.analysis_notebook_template,
                    entity_id=existing.id,
                    asset_id=asset.id,
                )
            clone_db = existing
        else:
            clone_db = AnalysisNotebookTemplate(
                name=notebook.name,
                description=notebook.description,
                scale=notebook.scale,
                specifications=notebook.specifications,
                assignment_id=notebook.assignment_id,
                authorized_project_id=project_id,
                authorized_public=False,
                created_by_id=db_user.id,
                updated_by_id=db_user.id,
            )
            repos.db.add(clone_db)
            repos.db.flush()
            repos.db.refresh(clone_db)

        virtual_lab_id = resolve_virtual_lab_id(user_context, project_id)
        storage = storages[StorageType.aws_s3_internal]
        s3_client = storage_client_factory(storage)

        for asset in notebook.assets:
            dst_key = build_s3_path(
                vlab_id=virtual_lab_id,
                proj_id=project_id,
                entity_type=EntityType.analysis_notebook_template,
                entity_id=clone_db.id,
                filename=asset.path,
                is_public=False,
            )
            copy_file(
                s3_client,
                src_bucket_name=storage.bucket,
                dst_bucket_name=storage.bucket,
                src_key=str(asset.full_path),
                dst_key=dst_key,
            )
            create_entity_asset_unverified(
                repos,
                entity=clone_db,
                filename=asset.path,
                content_type=asset.content_type,
                size=asset.size,
                sha256_digest=asset.sha256_digest.hex() if asset.sha256_digest else None,
                meta=asset.meta,
                label=asset.label,
                is_directory=asset.is_directory,
                storage_type=asset.storage_type,
                full_path=dst_key,
                status=asset.status,
                user_profile=user_context.profile,
                virtual_lab_id=virtual_lab_id,
            )
        repos.db.refresh(clone_db, ["assets"])
        created.append(AnalysisNotebookTemplateRead.model_validate(clone_db))
    return NotebookCloneResponse(created=created)
