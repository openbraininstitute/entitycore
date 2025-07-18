import uuid
from datetime import datetime

from app.filters.base import CustomFilter
from app.filters.common import (
    BrainRegionFilterMixin,
    EntityFilterMixin,
)
from app.filters.subject import SubjectFilterMixin


class ScientificArtifactFilter(
    CustomFilter, SubjectFilterMixin, BrainRegionFilterMixin, EntityFilterMixin
):
    experiment_date__lte: datetime | None = None
    experiment_date__gte: datetime | None = None
    contact_id: uuid.UUID | None = None
