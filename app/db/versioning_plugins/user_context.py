"""UserContext Plugin."""

from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session
from sqlalchemy_history.plugins import Plugin

from app.logger import L

if TYPE_CHECKING:
    import uuid

    from app.schemas.auth import UserContext


class UserContextPlugin(Plugin):
    def transaction_args(self, uow, session: Session) -> dict[str, Any]:  # noqa: ARG002, PLR6301
        from app.queries.utils import get_user  # noqa: PLC0415

        user_context: UserContext | None
        user_id: uuid.UUID | None = None
        if user_context := session.info.get("user_context"):
            # FIXME: # noqa: FIX001
            # the creation of a new agent would fail with: Session is already flushing
            # so the user_id is logged only if it already exists.
            # Alternative: ensure that the person is created at the beginning of the request,
            # and maybe update user_context with the user_id.
            # person = get_or_create_user_agent(db=session, user_profile=user_context.profile)
            person = get_user(db=session, subject_id=user_context.profile.subject)
            if person:
                user_id = person.id
        else:
            L.warning("UserContext not found!")
        return {
            "user_id": user_id,
            "remote_addr": None,
        }
