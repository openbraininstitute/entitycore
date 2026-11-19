"""Body of the admin create endpoints, with the check of the project in the payload."""

from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Body, Depends

from app.dependencies.virtual_lab_api import AdminVirtualLabClientDep
from app.utils.virtual_lab import ensure_project_exists


def _admin_create_depends(schema: Any) -> Any:
    """Return a FastAPI Depends parsing the body, and checking that its project exists."""

    def check_project(
        json_model: Annotated[schema, Body()],  # pyright: ignore[reportInvalidTypeForm]
        virtual_lab_client: AdminVirtualLabClientDep,
    ) -> Any:
        ensure_project_exists(virtual_lab_client, json_model.authorized_project_id)
        return json_model

    return Depends(check_project)


if TYPE_CHECKING:
    # Pyright doesn't follow __class_getitem__ → Annotated; this stub makes
    # AdminCreateDep[MySchema] type as Annotated[MySchema, Depends()].
    type AdminCreateDep[S] = Annotated[S, Depends()]
else:

    class AdminCreateDep:
        """Use as ``AdminCreateDep[MyAdminCreate]``, with a schema with ``authorized_project_id``.

        The body is validated as for ``Annotated[MyAdminCreate, Body()]``, then the project is
        checked with virtual-lab-manager (see ``ensure_project_exists``).
        """

        def __class_getitem__(cls, schema: Any) -> Any:
            """Build Annotated[schema, Depends(...)]."""
            return Annotated[schema, _admin_create_depends(schema)]
