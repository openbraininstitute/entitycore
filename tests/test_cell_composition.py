import pytest

from app.db.model import CellComposition
from app.db.types import EntityType

from .utils import PROJECT_ID, add_db, assert_request

ROUTE = "cell-composition"


@pytest.fixture
def cell_composition_id(db, brain_region_id, species_id, person_id):
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
    return row.id


def test_read_one(client, cell_composition_id):
    data = assert_request(client.get, url=f"{ROUTE}/{cell_composition_id}").json()
    assert data["name"] == "my-composition"
    assert "assets" in data
    assert data["type"] == EntityType.cell_composition

    data = assert_request(client.get, url=f"{ROUTE}").json()["data"][0]
    assert data["name"] == "my-composition"
    assert "assets" in data
    assert data["type"] == EntityType.cell_composition


def test_filtering(client, db, brain_region_id, species_id, person_id):
    row1 = add_db(
        db,
        CellComposition(
            name="my-composition-1",
            description="my-composition-1",
            brain_region_id=brain_region_id,
            species_id=species_id,
            created_by_id=person_id,
            updated_by_id=person_id,
            authorized_project_id=PROJECT_ID,
        ),
    )
    add_db(
        db,
        CellComposition(
            name="my-composition-2",
            description="my-composition-2",
            brain_region_id=brain_region_id,
            species_id=species_id,
            created_by_id=person_id,
            updated_by_id=person_id,
            authorized_project_id=PROJECT_ID,
        ),
    )
    data = assert_request(client.get, url=f"{ROUTE}", params={"name": "my-composition-1"}).json()[
        "data"
    ]
    assert len(data) == 1
    assert data[0]["name"] == "my-composition-1"
    assert data[0]["id"] == str(row1.id)
    assert "assets" in data[0]
    assert data[0]["type"] == EntityType.cell_composition
