from fastapi_filter.contrib.sqlalchemy import Filter

from app.db.model import Species, Strain


class SpeciesFilter(Filter):
    id: int | None = None
    name: str | None = None

    class Constants(Filter.Constants):
        model = Species


class StrainFilter(Filter):
    id: int | None = None
    name: str | None = None

    class Constants(Filter.Constants):
        model = Strain
