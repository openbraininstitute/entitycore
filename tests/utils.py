from contextlib import contextmanager

from app.application import app
from app.routers.auth import check_project_id

BEARER_TOKEN = {"Authorization": "Bearer this is a fake token"}

PROJECT_HEADERS = {
    "virtual-lab-id": "9c6fba01-2c6f-4eac-893f-f0dc665605c5",
    "project-id": "0e1181f3-1e19-4c4c-9b13-9ec372f690de",
}


@contextmanager
def allow_all_access():
    orig = dict(app.dependency_overrides)

    def ok():
        return True

    app.dependency_overrides[check_project_id] = ok

    yield

    app.dependency_overrides = orig
