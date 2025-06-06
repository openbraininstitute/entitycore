import uuid
from uuid import UUID
from functools import partial
from typing import TYPE_CHECKING, Annotated, Any

import sqlalchemy as sa
from fastapi import Query
from sqlalchemy.orm import (
    aliased,
    joinedload,
    raiseload,
    selectinload,
)

from app.db.model import (
    Agent,
    Contribution,
    MeasurementAnnotation,
    MeasurementKind,
    CellMorphology,
)
from app.db.types import MorphologyStructureType
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.morphology import MorphologyFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.queries.factory import query_params_factory
from app.schemas.morphology import (
    CellMorphologyAnnotationExpandedRead,
    CellMorphologyCreate,
    CellMorphologyRead,
    ComputationallySynthesized,
    ComputationallySynthesizedCreate,
    DigitalReconstruction,
    DigitalReconstructionCreate,
    ModifiedReconstruction,
    ModifiedReconstructionCreate,
    Placeholder,
    PlaceholderCreate,
)
from app.schemas.types import ListResponse
from app.schemas.agent import PersonRead

if TYPE_CHECKING:
    from app.filters.base import Aliases

morphology_type_to_schema = {
    MorphologyStructureType.digital_reconstruction: DigitalReconstruction,
    MorphologyStructureType.modified: ModifiedReconstruction,
    MorphologyStructureType.computationally_synthesized: ComputationallySynthesized,
    MorphologyStructureType.placeholder: Placeholder,
    MorphologyStructureType.generic: CellMorphologyRead,
}

schema_map = {
    MorphologyStructureType.digital_reconstruction: DigitalReconstructionCreate,
    MorphologyStructureType.modified: ModifiedReconstructionCreate,
    MorphologyStructureType.computationally_synthesized: ComputationallySynthesizedCreate,
    MorphologyStructureType.placeholder: PlaceholderCreate,
    MorphologyStructureType.generic: CellMorphologyCreate,
}


def _load_from_db(query: sa.Select, *, expand_measurement_annotation: bool = False) -> sa.Select:
    """Return the query with the required options to load the data."""
    query = query.options(
        joinedload(CellMorphology.brain_region),
        selectinload(CellMorphology.contributions).selectinload(Contribution.agent),
        selectinload(CellMorphology.contributions).selectinload(Contribution.role),
        joinedload(CellMorphology.mtypes),
        joinedload(CellMorphology.license),
        joinedload(CellMorphology.species, innerjoin=True),
        joinedload(CellMorphology.strain),
        selectinload(CellMorphology.assets),
        joinedload(CellMorphology.created_by),
        joinedload(CellMorphology.updated_by),
        raiseload("*"),
    )
    if expand_measurement_annotation:
        query = query.options(
            joinedload(CellMorphology.measurement_annotation)
            .selectinload(MeasurementAnnotation.measurement_kinds)
            .selectinload(MeasurementKind.measurement_items),
            joinedload(CellMorphology.measurement_annotation).contains_eager(
                MeasurementAnnotation.entity
            ),
        )
    return query


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    expand: Annotated[set[str] | None, Query()] = None,
) -> CellMorphologyRead | CellMorphologyAnnotationExpandedRead:
    if expand and "measurement_annotation" in expand:
        response_schema_class = CellMorphologyAnnotationExpandedRead
        apply_operations = partial(_load_from_db, expand_measurement_annotation=True)
    else:
        response_schema_class = CellMorphologyRead
        apply_operations = partial(_load_from_db, expand_measurement_annotation=False)
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=CellMorphology,
        authorized_project_id=user_context.project_id,
        response_schema_class=response_schema_class,
        apply_operations=apply_operations,
    )


def create_one(
    db: SessionDep,
    project_id: UUID,
    virtual_lab_id: UUID,
    user_id: str,
    body: dict[str, Any],
) -> CellMorphologyRead:
  
    # Validate against specific schema based on morphology_type
    try:
        structure_type = MorphologyStructureType(body.get("morphology_type"))
        schema = schema_map[structure_type]
        validated_body = schema(**body)
    except (KeyError, ValueError, ValidationError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid morphology_type or schema: {e!s}")

    # Prepare extra_data
    extra_data = {
        "reconstruction_method": validated_body.reconstruction_method.dict() if hasattr(validated_body, "reconstruction_method") else None,
        "pipeline_state": validated_body.pipeline_state if hasattr(validated_body, "pipeline_state") else None,
        "is_related_to": validated_body.is_related_to if hasattr(validated_body, "is_related_to") else [],
        "published_in": body.get("published_in", {}) or {},
    }

    # Define allowed fields for CellMorphology
    allowed_fields = {
        "type",
        "brain_region_id",
        "species_id",
        "license_id",
        "subject_id",
        "authorized_project_id",
        "authorized_public",
        "name",
        "description",
        "experiment_date",
        "published_in",
        "validation_tags",
        "contact_id",
        "legacy_id",
        #"mtypes",
        "structure_type",
    }

    # Prepare json_model_data
    json_model_data = {
        k: v for k, v in validated_body.dict(exclude_unset=True).items()
        if k in allowed_fields
    }

    # Ensure required fields
    json_model_data.setdefault("mtypes", [])
    json_model_data.setdefault("authorized_project_id", project_id)
    json_model_data.setdefault("name", body.get("name", "Unnamed Morphology"))
    json_model_data.setdefault("published_in", extra_data["published_in"])
    json_model_data.setdefault("validation_tags", extra_data["validation_tags"])
    json_model_data.setdefault("license_id", body.get("license_id"))
    json_model_data.setdefault("structure_type", validated_body.morphology_type)
    json_model_data.setdefault("authorized_public", body.get("authorized_public", False))
    json_model_data.setdefault("species_id", body.get("species_id"))
    json_model_data.setdefault("brain_region_id", body.get("brain_region_id"))
    json_model_data.setdefault("description", body.get("description"))
    json_model_data.setdefault("subject_id", body.get("subject_id"))
    json_model_data.setdefault("experiment_date", body.get("experiment_date"))
    json_model_data.setdefault("contact_id", body.get("contact_id"))
    json_model_data["id"] = uuid.uuid4()  # Generate UUID for entity/scientific_artifact

    # Fetch createdBy and updatedBy Person objects and add them to json_model_data
    try:
        if user_id:
            created_by_person = db.execute(sa.select(Person).filter_by(id=UUID(user_id))).scalar_one_or_none()
            if not created_by_person:
                raise HTTPException(status_code=422, detail=f"Invalid createdBy user_id: {user_id}")
            json_model_data["createdBy"] = PersonRead.model_validate(created_by_person).model_dump()
            json_model_data["updatedBy"] = PersonRead.model_validate(created_by_person).model_dump() # Assume updatedBy is same as createdBy initially
        else:
            raise HTTPException(status_code=401, detail="User ID is required for createdBy and updatedBy fields.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user details: {e!s}")

    # Validate foreign keys (excluding createdBy_id/updatedBy_id which are now objects)
    try:
        if json_model_data.get("species_id"):
            species = db.execute(sa.select(Species).filter_by(id=json_model_data["species_id"])).scalar_one_or_none()
            if not species:
                raise HTTPException(status_code=422, detail=f"Invalid species_id: {json_model_data['species_id']}")
        if json_model_data.get("brain_region_id"):
            brain_region_query = sa.select(BrainRegion).filter_by(id=json_model_data["brain_region_id"])
            brain_region = db.execute(brain_region_query).scalar_one_or_none()
            if not brain_region:
                raise HTTPException(status_code=422, detail=f"Invalid brain_region_id: {json_model_data['brain_region_id']}")
        if json_model_data.get("license_id"):
            license = db.execute(sa.select(License).filter_by(id=json_model_data["license_id"])).scalar_one_or_none()
            if not license:
                raise HTTPException(status_code=422, detail=f"Invalid license_id: {json_model_data['license_id']}")
        if json_model_data.get("contact_id"):
            person = db.execute(sa.select(Person).filter_by(id=json_model_data["contact_id"])).scalar_one_or_none()
            if not person:
                raise HTTPException(status_code=422, detail=f"Invalid contact_id: {json_model_data['contact_id']}")
                  
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Foreign key validation error: {e!s}")

    # Create CellMorphologyCreate instance
    try:
        # Pass the json_model_data which now includes the full Person objects
        json_model = CellMorphologyCreate(**json_model_data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {e!s}")

    # Transform fields for database storage
    db_model_data = json_model.dict(exclude_unset=True)
    if "published_in" in db_model_data and isinstance(db_model_data["published_in"], dict):
        db_model_data["published_in"] = db_model_data["published_in"].get("original_source_location", "")
    db_model_data["creation_date"] = datetime.utcnow()
    db_model_data["update_date"] = datetime.utcnow()
#    if "experiment_date" in db_model_data and isinstance(db_model_data["experiment_date"], str):
#        db_model_data["experiment_date"] = datetime.fromisoformat(db_model_data["experiment_date"])

    # Convert createdBy and updatedBy objects back to IDs for DB storage
    db_model_data["createdBy_id"] = db_model_data["createdBy"]["id"] if db_model_data.get("createdBy") else None
    db_model_data["updatedBy_id"] = db_model_data["updatedBy"]["id"] if db_model_data.get("updatedBy") else None
    db_model_data.pop("createdBy", None) # Remove the object field
    db_model_data.pop("updatedBy", None) # Remove the object field

    # Create the CellMorphology instance
    try:
        row = CellMorphology(**db_model_data)
        
        db.add(row)
     
        db.commit()
    
        db.refresh(row)
       
    except IntegrityError as e:
     
        db.rollback()
        raise HTTPException(status_code=422, detail=f"Database integrity error: {e!s}")
    except Exception as e:
     
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e!s}")

    # Reload row with relationships
    try:
        query = sa.select(CellMorphology).options(
            joinedload(CellMorphology.license),
            joinedload(CellMorphology.brain_region),
            joinedload(CellMorphology.createdBy), # Ensure createdBy relationship is loaded
            joinedload(CellMorphology.updatedBy)  # Ensure updatedBy relationship is loaded
        ).filter(CellMorphology.id == row.id)

        row = db.execute(query).unique().scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=500, detail="Failed to reload created record")
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Reload error: {e!s}")

    # Log row contents for debugging
    row_fields = [
        "id", "type","authorized_project_id", "license_id", "creation_date", "name",
        "published_in", "validation_tags", "morphology_type", "brain_region_id",
        "species_id", "subject_id", "authorized_public", "description",
        "createdBy_id", "updatedBy_id", "experiment_date", "contact_id", "legacy_id"
    ]
    row_dict = {key: getattr(row, key, None) for key in row_fields}
   

    # Prepare response data
    response_data = {
        "id": row.id,
        "type": row.type,
        "authorized_project_id": row.authorized_project_id or project_id,
        "license": LicenseRead.model_validate(row.license).model_dump() if row.license else None,
        "license_id": row.license_id,
        "creation_date": row.creation_date,
        "name": row.name,
        "published_in": extra_data["published_in"],
        "validation_tags": extra_data["validation_tags"],
        "mtypes": [],
        "structure_type": row.morphology_type,
        "reconstruction_method": extra_data["reconstruction_method"],
        "pipeline_state": extra_data["pipeline_state"],
        "is_related_to": extra_data["is_related_to"],
        # Add brain_region object
        "brain_region": {
            "id": row.brain_region.id,
            "name": row.brain_region.name,
            "acronym": row.brain_region.acronym,
            "annotation_value": row.brain_region.annotation_value,
            "color_hex_triplet": row.brain_region.color_hex_triplet,
            "parent_structure_id": row.brain_region.parent_structure_id,
            "hierarchy_id": row.brain_region.hierarchy_id,
            "creation_date": row.brain_region.creation_date,
            "update_date": row.brain_region.update_date,
        } if row.brain_region else None,
        # Add createdBy and updatedBy objects, validated by PersonRead
        "createdBy": PersonRead.model_validate(row.createdBy).model_dump() if row.createdBy else None,
        "updatedBy": PersonRead.model_validate(row.updatedBy).model_dump() if row.updatedBy else None,
    }

    # Include additional fields from row
    for key in ["description", "subject_id", "authorized_public", "experiment_date", "contact_id", "legacy_id", "species_id"]:
        if hasattr(row, key) and getattr(row, key) is not None:
            response_data[key] = getattr(row, key)

    # Remove brain_region_id, createdBy_id, updatedBy_id since objects are now included
    response_data.pop("brain_region_id", None)
    # response_data.pop("createdBy_id", None) # These are not in response_data from row directly
    # response_data.pop("updatedBy_id", None) # These are not in response_data from row directly

   

    # Validate and return using appropriate schema
    try:
        response_schema = MORPHOLOGY_TYPE_TO_SCHEMA.get(validated_body.morphology_type, CellMorphologyRead)
 
        validated_response = response_schema.model_validate(response_data)
        
        return validated_response
    except ValidationError as e:
      
        # Fallback to CellMorphologyRead
        try:
         
            validated_response = CellMorphologyRead.model_validate(response_data)
         
            return validated_response
        except ValidationError as fallback_e:
           
            raise HTTPException(status_code=500, detail=f"Response validation error: {e!s}")
    except Exception as e:
       
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e!s}")


def read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    morphology_filter: MorphologyFilterDep,
    search: SearchDep,
    with_facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[CellMorphologyRead]:
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    aliases: Aliases = {
        Agent: {
            "contribution": agent_alias,
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
    }
    facet_keys = [
        "brain_region",
        "species",
        "created_by",
        "updated_by",
        "contribution",
        "mtype",
        "strain",
    ]
    filter_keys = [
        *facet_keys,
        "measurement_annotation",
        "measurement_annotation.measurement_kind",
        "measurement_annotation.measurement_kind.measurement_item",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=CellMorphology,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        db_model_class=CellMorphology,
        authorized_project_id=user_context.project_id,
        with_search=search,
        with_in_brain_region=in_brain_region,
        facets=with_facets,
        aliases=aliases,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load_from_db,
        pagination_request=pagination_request,
        response_schema_class=CellMorphologyRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=morphology_filter,
        filter_joins=filter_joins,
    )
