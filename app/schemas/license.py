from pydantic import UUID4, ConfigDict

from app.schemas.base import NameDescriptionMixin, Schema
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead, NestedIdentifiableRead
from app.schemas.utils import make_update_schema


class LicenseBaseMixin(NameDescriptionMixin):
    label: str


class LicenseCreate(LicenseBaseMixin, IdentifiableCreate):
    model_config = ConfigDict(from_attributes=True)
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
    license_id: UUID4 | None = None


class LicensedCreateMixin(Schema):
    license_id: UUID4 | None = None


class LicensedReadMixin(Schema):
    license: NestedLicenseRead | None
