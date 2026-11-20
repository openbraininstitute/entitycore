import uuid

from app.schemas.base import NameDescriptionMixin
from app.schemas.brain_region import NestedBrainRegionRead
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.entity import EntityCreate, EntityRead
from app.schemas.license import LicenseCreateMixin, LicenseReadMixin
from app.schemas.subject import NestedSubjectRead
from app.schemas.utils import make_update_schema


class GenericDatasetBase(NameDescriptionMixin):
    pass


class GenericDatasetCreate(GenericDatasetBase, EntityCreate, LicenseCreateMixin):
    subject_id: uuid.UUID | None = None
    brain_region_id: uuid.UUID | None = None


GenericDatasetUserUpdate = make_update_schema(
    GenericDatasetCreate,
    "GenericDatasetUserUpdate",
)  # pyright : ignore [reportInvalidTypeForm]

GenericDatasetAdminUpdate = make_update_schema(
    GenericDatasetCreate,
    "GenericDatasetAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class GenericDatasetRead(
    GenericDatasetBase,
    EntityRead,
    LicenseReadMixin,
    ContributionReadWithoutEntityMixin,
):
    subject: NestedSubjectRead | None = None
    brain_region: NestedBrainRegionRead | None = None
