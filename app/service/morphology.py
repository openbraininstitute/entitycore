import uuid
from typing import TYPE_CHECKING, Annotated

import sqlalchemy as sa
from fastapi import Query
from sqlalchemy.orm import (
    joinedload,
    raiseload,
    selectinload,
)

from app.db.auth import constrain_to_accessible_entities
from app.db.model import (
    Agent,
    Contribution,
    MorphologyFeatureAnnotation,
    MorphologyMeasurement,
    MTypeClass,
    MTypeClassification,
    CellMorphology,
    Species,
    Strain,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import FacetsDep, PaginationQuery, SearchDep
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.morphology import MorphologyFilterDep
from app.queries.common import router_create_one, router_read_many
from app.schemas.morphology import (
    CellMorphologyAnnotationExpandedRead,
    CellMorphologyCreate,
    CellMorphologyRead,
)
from app.schemas.types import ListResponse

from typing import Annotated, Union
from fastapi import APIRouter, Body
from app.db.types import MorphologyType 
from app.schemas.morphology import MethodsType 

if TYPE_CHECKING:
    from app.queries.common import FacetQueryParams


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    expand: Annotated[set[str] | None, Query()] = None,
) -> CellMorphologyRead:
    """
    Read a single CellMorphology object by ID and dynamically return its subclass schema.
    """
    with ensure_result(error_message="CellMorphology not found"):
        query = constrain_to_accessible_entities(
            sa.select(CellMorphology), user_context.project_id
        ).filter(CellMorphology.id == id_)

        if expand and "morphology_feature_annotation" in expand:
            query = query.options(
                joinedload(CellMorphology.morphology_feature_annotation)
                .selectinload(MorphologyFeatureAnnotation.measurements)
                .selectinload(MorphologyMeasurement.measurement_serie)
            )

        query = (
            query.options(joinedload(CellMorphology.brain_region))
            .options(
                selectinload(CellMorphology.contributions).selectinload(
                    Contribution.agent
                )
            )
            .options(
                selectinload(CellMorphology.contributions).selectinload(Contribution.role)
            )
            .options(joinedload(CellMorphology.mtypes))
            .options(joinedload(CellMorphology.license))
            .options(joinedload(CellMorphology.species))
            .options(joinedload(CellMorphology.strain))
            .options(selectinload(CellMorphology.assets))
            .options(raiseload("*"))
        )

        row = db.execute(query).unique().scalar_one()

    # Expand annotation if requested
    if expand and "morphology_feature_annotation" in expand:
        return CellMorphologyAnnotationExpandedRead.model_validate(row)

    # === Dynamic subclass mapping based on attributes ===
    # These conditions must reflect actual columns in your DB model

    # Determine the base class based on the type
    if hasattr(row, "score_dict") and hasattr(row, "provenance"):
        base_class = ComputationallySynthesized
        expanded_class = ComputationallySynthesizedAnnotationExpandedRead
    elif hasattr(row, "pipeline_state"):
        base_class = DigitalReconstruction
        expanded_class = DigitalReconstructionAnnotationExpandedRead
    elif hasattr(row, "method") and isinstance(row.method, MethodsType):
        base_class = ModifiedReconstruction
        expanded_class = ModifiedReconstructionAnnotationExpandedRead
    elif hasattr(row, "is_related_to") and not hasattr(row, "pipeline_state") and not hasattr(row, "method"):
        base_class = Placeholder
        expanded_class = PlaceholderAnnotationExpandedRead
    else:
        base_class = CellMorphologyRead
        expanded_class = CellMorphologyAnnotationExpandedRead

    # Expand annotation if requested
    if expand and "morphology_feature_annotation" in expand:
        return expanded_class.model_validate(row)
    
    return base_class.model_validate(row)



from app.schemas.morphology import (
    CellMorphologyCreate,
    DigitalReconstructionCreate,
    ModifiedReconstructionCreate,
    ComputationallySynthesizedCreate,
    PlaceholderCreate,
    DigitalReconstruction,
    ModifiedReconstruction,
    ComputationallySynthesized,
    Placeholder,
    CellMorphologyRead,
    ComputationallySynthesizedAnnotationExpandedRead,  
    PlaceholderAnnotationExpandedRead,  
    DigitalReconstructionAnnotationExpandedRead,  
    ModifiedReconstructionAnnotationExpandedRead,  
)

MorphologyCreateType = Union[
    DigitalReconstructionCreate,
    ModifiedReconstructionCreate,
    ComputationallySynthesizedCreate,
    PlaceholderCreate,
    CellMorphologyCreate,
]


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    reconstruction: CellMorphologyCreate,
) -> CellMorphologyRead:
    # Determine subclass and morphology_type
    if isinstance(reconstruction, DigitalReconstructionCreate):
        schema_class = DigitalReconstruction
        morphology_type = MorphologyType.DIGITAL
    elif isinstance(reconstruction, ModifiedReconstructionCreate):
        schema_class = ModifiedReconstruction
        morphology_type = MorphologyType.MODIFIED
    elif isinstance(reconstruction, ComputationallySynthesizedCreate):
        schema_class = ComputationallySynthesized
        morphology_type = MorphologyType.COMPUTATIONAL
    elif isinstance(reconstruction, PlaceholderCreate):
        schema_class = Placeholder
        morphology_type = MorphologyType.PLACEHOLDER
    else:
        schema_class = CellMorphologyRead
        morphology_type = MorphologyType.GENERIC

    return router_create_one(
        db=db,
        db_model_class=CellMorphology,
        authorized_project_id=user_context.project_id,
        json_model=reconstruction,
        response_schema_class=schema_class,
        extra_data={"morphology_type": morphology_type},
    )

MORPHOLOGY_TYPE_TO_SCHEMA = {
    MorphologyType.DIGITAL: DigitalReconstruction,
    MorphologyType.MODIFIED: ModifiedReconstruction,
    MorphologyType.COMPUTATIONAL: ComputationallySynthesized,
    MorphologyType.PLACEHOLDER: Placeholder,
    MorphologyType.GENERIC: CellMorphologyRead,
}

def read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    morphology_filter: MorphologyFilterDep,
    search: SearchDep,
    with_facets: FacetsDep,
) -> ListResponse[CellMorphologyRead]:

    name_to_facet_query_params: dict[str, FacetQueryParams] = {
        "mtype": {"id": MTypeClass.id, "label": MTypeClass.pref_label},
        "species": {"id": Species.id, "label": Species.name},
        "strain": {"id": Strain.id, "label": Strain.name},
        "contribution": {
            "id": Agent.id,
            "label": Agent.pref_label,
            "type": Agent.type,
        },
    }

    def data_query_ops(q):
        return (
            q.options(joinedload(CellMorphology.species, innerjoin=True))
            .options(joinedload(CellMorphology.strain))
            .options(selectinload(CellMorphology.contributions).selectinload(Contribution.agent))
            .options(selectinload(CellMorphology.contributions).selectinload(Contribution.role))
            .options(joinedload(CellMorphology.mtypes))
            .options(joinedload(CellMorphology.brain_region))
            .options(joinedload(CellMorphology.license))
            .options(selectinload(CellMorphology.assets))
            .options(raiseload("*"))
        )

    def filter_query_ops(q):
        return (
            q.join(Species, CellMorphology.species_id == Species.id)
            .outerjoin(Strain, CellMorphology.strain_id == Strain.id)
            .outerjoin(Contribution, CellMorphology.id == Contribution.entity_id)
            .outerjoin(Agent, Contribution.agent_id == Agent.id)
            .outerjoin(MTypeClassification, CellMorphology.id == MTypeClassification.entity_id)
            .outerjoin(MTypeClass, MTypeClass.id == MTypeClassification.mtype_class_id)
        )

    def response_schema_transformer(row: CellMorphology) -> CellMorphologyRead:
        morphology_type = getattr(row, "morphology_type", None)
        if morphology_type is None or not isinstance(morphology_type, MorphologyType):
            schema_class = CellMorphologyRead
        else:
            schema_class = MORPHOLOGY_TYPE_TO_SCHEMA.get(morphology_type, CellMorphologyRead)
        if schema_class is None:
            raise ValueError("Schema class cannot be None")
        return schema_class.model_validate(row)

    return router_read_many(
        db=db,
        db_model_class=CellMorphology,
        authorized_project_id=user_context.project_id,
        with_search=search,
        facets=with_facets,
        aliases=None,
        apply_filter_query_operations=filter_query_ops,
        apply_data_query_operations=data_query_ops,
        pagination_request=pagination_request,
        response_schema_class=CellMorphologyRead,
        response_schema_transformer=response_schema_transformer,  
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=morphology_filter,
    )
