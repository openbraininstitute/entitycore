from app.db.model import CellComposition
from app.db.types import EntityType

from .utils import PROJECT_ID, add_db, assert_request

ROUTE = "cell-composition"


def test_read_one(client, db, brain_region_id, species_id, person_id):
    row = add_db(
        db,
        CellComposition(
            name="my-composition",
            description="my-composition",
            brain_region_id=brain_region_id,
            species_id=species_id,
            created_by_id=person_id,
            updated_by_id=person_id,
            authorized_project_id=PROJECT_ID,
        ),
    )

    data = assert_request(client.get, url=f"{ROUTE}/{row.id}").json()
    assert data["name"] == "my-composition"
    assert "assets" in data
    assert data["type"] == EntityType.cell_composition
