from typing import Self
from uuid import UUID

import jwt
import regex as re
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict

from app.errors import AuthErrorReason
from app.logger import L


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

    def find_virtual_lab_id(self, project_id: UUID | None) -> UUID | None:
        """Return the virtual_lab_id if authorized for the specified project_id."""
        pattern = rf"/proj/([0-9a-fA-F-]+)/{re.escape(str(project_id))}/(admin|member)"

        for s in self.groups:
            match = re.search(pattern, s)
            if match:
                return UUID(match.group(1))
        return None


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
    model_config = ConfigDict(frozen=True)
    profile: UserProfile
    expiration: float | None
    is_authorized: bool
    is_service_admin: bool = False
    auth_error_reason: AuthErrorReason | None = None


class UserContext(UserContextBase):
    """User Context."""

    virtual_lab_id: UUID | None = None
    project_id: UUID | None = None


class UserContextWithProjectId(UserContextBase):
    """User Context with valid virtual_lab_id and project_id."""

    virtual_lab_id: UUID
    project_id: UUID
