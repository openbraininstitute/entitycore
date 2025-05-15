from pydantic import BaseModel, ConfigDict
from typing import Optional, Set  

class Validation(BaseModel):
    entity_type: str  # from predetermined vocabulary (an entity class in db)  
    must_pass_to_upload: Optional[Set[str]] = None   # set of validation script paths in  github repo. Each has a function with output pass or fail.  Optional output (log fails)  If any fails, the entity can’t be uploaded to the database.
    must_run_upon_upload: Optional[Set[str]] = None #set of validation script paths in github repo that will be launched when uploading an artifact. The result will be available as annotation to the entity.

    must_pass_to_simulate: Optional[Set[str]] = None  #set of validation script paths in github repo that must pass to simulate. Will be launched when uploading an artifact, the result will be available as annotation to the entity.

