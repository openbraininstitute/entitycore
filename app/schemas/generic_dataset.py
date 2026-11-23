import uuid

from app.schemas.base import AuthorizedProjectIdMixin, NameDescriptionMixin
from app.schemas.brain_region import NestedBrainRegionRead
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.entity import EntityRead, PrivateEntityCreate
from app.schemas.license import LicenseCreateMixin, LicenseReadMixin
from app.schemas.subject import NestedSubjectRead
from app.schemas.utils import make_update_schema


class GenericDatasetBase(NameDescriptionMixin):
    pass


class GenericDatasetCreate(GenericDatasetBase, PrivateEntityCreate, LicenseCreateMixin):
    subject_id: uuid.UUID | None = None
    brain_region_id: uuid.UUID | None = None


class GenericDatasetAdminCreate(AuthorizedProjectIdMixin, GenericDatasetCreate):
    pass


GenericDatasetUserUpdate = make_update_schema(
    GenericDatasetCreate,
    "GenericDatasetUserUpdate",
)  # pyright : ignore [reportInvalidTypeForm]

# authorized_public is excluded also for admins, because the dataset must always be private
GenericDatasetAdminUpdate = make_update_schema(
    GenericDatasetCreate,
    "GenericDatasetAdminUpdate",
)  # pyright : ignore [reportInvalidTypeForm]


class GenericDatasetRead(
    GenericDatasetBase,
    EntityRead,
    LicenseReadMixin,
    ContributionReadWithoutEntityMixin,
):
    subject: NestedSubjectRead | None = None
    brain_region: NestedBrainRegionRead | None = None
