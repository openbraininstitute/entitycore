from contextlib import contextmanager

from app.application import app
from app.routers.auth import check_project_id

BEARER_TOKEN = {"Authorization": "Bearer this is a fake token"}

PROJECT_HEADERS = {
    "virtual-lab-id": "9c6fba01-2c6f-4eac-893f-f0dc665605c5",
    "project-id": "ee86d4a0-eaca-48ca-9788-ddc450250b15",
}


@contextmanager
def allow_all_access():
    orig = dict(app.dependency_overrides)

    def ok():
        return True

    app.dependency_overrides[check_project_id] = ok

    yield

    app.dependency_overrides = orig
