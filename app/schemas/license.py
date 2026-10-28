from uuid import UUID

from app.schemas.base import NameDescriptionMixin, Schema
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead, NestedIdentifiableRead
from app.schemas.utils import make_update_schema


class LicenseBaseMixin(NameDescriptionMixin):
    label: str


class LicenseCreate(LicenseBaseMixin, IdentifiableCreate):
    label: str


class NestedLicenseRead(LicenseBaseMixin, NestedIdentifiableRead):
    pass


class LicenseRead(LicenseBaseMixin, IdentifiableRead):
    pass


LicenseAdminUpdate = make_update_schema(
    LicenseCreate,
    "LicenseAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class LicenseReadMixin:
    license: NestedLicenseRead | None = None


class LicenseCreateMixin:
    license_id: UUID | None = None


class LicensedCreateMixin(Schema):
    license_id: UUID | None = None


class LicensedReadMixin(Schema):
    license: NestedLicenseRead | None
