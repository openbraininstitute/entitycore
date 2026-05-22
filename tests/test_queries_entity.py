from uuid import UUID

from app.db.model import Circuit
from app.queries.entity import get_writable_entity

from tests.utils import PROJECT_ID


def test_get_writable_entity_for_update(db, circuit):
    entity = get_writable_entity(
        db,
        Circuit,
        circuit.id,
        UUID(PROJECT_ID),
        for_update=True,
    )
    assert entity.id == circuit.id
