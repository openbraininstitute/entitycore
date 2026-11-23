from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.schemas.base import AuthorizedProjectIdMixin
from app.schemas.utils import make_update_schema


class SimulationGenerationCreate(ActivityCreate):
    pass


class SimulationGenerationAdminCreate(AuthorizedProjectIdMixin, SimulationGenerationCreate):
    pass


class SimulationGenerationRead(ActivityRead):
    pass


class SimulationGenerationUserUpdate(ActivityUpdate):
    pass


SimulationGenerationAdminUpdate = make_update_schema(
    SimulationGenerationCreate,
    "SimulationGenerationAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
