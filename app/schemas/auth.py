import re
from enum import StrEnum, auto
from typing import Self
from uuid import UUID

import jwt
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict

from app.errors import AuthErrorReason
from app.logger import L

PROJECT_REGEX = re.compile(
    r"^/proj/(?P<vlab>[0-9a-fA-F-]+)/(?P<proj>[0-9a-fA-F-]+)/(?P<role>admin|member)$"
)


class CacheKey(BaseModel):
    """Cache key for UserContext."""

    model_config = ConfigDict(frozen=True)
    virtual_lab_id: UUID | None
    project_id: UUID | None
    scheme: str
    token_digest: str


class UserInfoBase(BaseModel):
    """Basic user info keycloak information."""

    sub: UUID
    name: str | None = None
    preferred_username: str
    exp: float | None = None
    given_name: str | None = None
    family_name: str | None = None


class DecodedToken(UserInfoBase):
    """Decoded JWT token.

    Only a subset of the claims is extracted.
    """

    @classmethod
    def from_jwt(cls, token: HTTPAuthorizationCredentials) -> Self | None:
        try:
            # the signature can be ignored because the token will be validated with KeyCloak
            decoded = jwt.decode(token.credentials, options={"verify_signature": False})
            return cls.model_validate(decoded)
        except Exception as e:  # noqa: BLE001
            L.info("Unable to decode token as JWT [{}]", e)
        return None


class UserRole(StrEnum):
    """Keycloak user role."""

    admin = auto()
    member = auto()


class UserProjectGroup(BaseModel):
    """Keycloak user group."""

    model_config = ConfigDict(frozen=True)

    virtual_lab_id: UUID
    project_id: UUID
    role: UserRole

    def __repr__(self):
        """Return the keycloak str group."""
        return f"/{self.virtual_lab_id}/{self.project_id}/{self.role}"

    def __hash__(self):
        """Return hash."""
        return hash(self.__repr__())

    def __eq__(self, other):
        """Return true if groups are the same."""
        return self.__repr__() == other.__repr__()


class UserInfoResponse(UserInfoBase):
    """UserInfoResponse model received from KeyCloak.

    Built from a KeyCloak response that should look like:

    {
        "email": "john.doe@example.com",
        "email_verified": false,
        "family_name": "Doe",
        "given_name": "John",
        "groups": [
            "/BBP-USERS",
            "/proj/$vlab_id/$project_id/admin",
            ...
            "/vlab/$vlab_id/admin",
            ...
        ],
        "name": "John Doe",
        "preferred_username": "johndoe",
        "sub": "83e509d1-d579-4d7e-bfe7-a0cf96ac17bf"
    }
    """

    groups: set[str] = set()

    def is_service_admin(self, service_name: str) -> bool:
        """Return True if admin for the specified service."""
        return not self.groups.isdisjoint(
            [
                f"/service/{service_name}/admin",
                "/service/*/admin",
            ]
        )

    def is_service_maintainer(self, service_name: str) -> bool:
        """Return True if admin for the specified service."""
        return f"/service/{service_name}/maintainer" in self.groups

    def is_authorized_for(self, virtual_lab_id: UUID | None, project_id: UUID | None) -> bool:
        """Return True if authorized for the specified virtual_lab_id and project_id."""
        match (virtual_lab_id, project_id):
            case (None, None):
                # virtual_lab_id and project_id are not specified
                return True
            case (None, UUID()):
                # project_id cannot be specified without virtual_lab_id
                return False
            case (UUID(), None):
                return not self.groups.isdisjoint(
                    [
                        f"/vlab/{virtual_lab_id}/admin",
                        f"/vlab/{virtual_lab_id}/member",
                    ]
                )
            case _:
                return not self.groups.isdisjoint(
                    [
                        f"/proj/{virtual_lab_id}/{project_id}/admin",
                        f"/proj/{virtual_lab_id}/{project_id}/member",
                    ]
                )

    def virtual_lab_from_project_id(self, project_id: UUID) -> UUID | None:
        for s in self.groups:
            if (match := PROJECT_REGEX.match(s)) and match.group("proj") == str(project_id):
                return UUID(match.group("vlab"))
        return None

    def user_project_groups(self) -> set[UserProjectGroup]:
        """Return the keycloak groups the user is authorized for."""
        return {
            UserProjectGroup(
                virtual_lab_id=UUID(match.group("vlab")),
                project_id=UUID(match.group("proj")),
                role=UserRole(match.group("role")),
            )
            for s in self.groups
            if (match := PROJECT_REGEX.match(s))
        }


class UserProfile(BaseModel):
    """User profile representing a keycloak user."""

    name: str
    subject: UUID
    given_name: str | None = None
    family_name: str | None = None

    @classmethod
    def from_user_info(cls, info: UserInfoBase):
        return cls(
            subject=info.sub,
            name=info.name or info.preferred_username,
            given_name=info.given_name,
            family_name=info.family_name,
        )

    @classmethod
    def unknown(cls):
        return cls(
            subject=UUID(int=0, version=4),
            name="Unknown",
        )


class UserContextBase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    profile: UserProfile
    expiration: float | None
    is_authorized: bool
    is_service_admin: bool = False
    is_service_maintainer: bool = False
    auth_error_reason: AuthErrorReason | None = None


class UserContext(UserContextBase):
    """User Context."""

    virtual_lab_id: UUID | None = None
    project_id: UUID | None = None
    user_project_groups: list[UserProjectGroup] = []

    @property
    def user_project_ids(self) -> list[UUID]:
        """Return all projects that the user has access to regardless of role."""
        return [g.project_id for g in self.user_project_groups]

    @property
    def project_member_ids(self):
        """Return the project ids for which the user is a member."""
        return [g.project_id for g in self.user_project_groups if g.role == UserRole.member]

    @property
    def project_admin_ids(self):
        """Return the project ids for which the user is an admin."""
        return [g.project_id for g in self.user_project_groups if g.role == UserRole.admin]


class UserContextWithProjectId(UserContextBase):
    """User Context with valid virtual_lab_id and project_id."""

    virtual_lab_id: UUID
    project_id: UUID
