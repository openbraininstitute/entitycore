import sqlalchemy as sa

from app.db.auth import constrain_to_private_entities
from app.db.model import Circuit


def test_constrain_to_private_entities(db, user_context_user_1, circuit):
    query = constrain_to_private_entities(
        query=sa.select(Circuit),
        user_context=user_context_user_1,
        db_model_class=Circuit,
    )
    rows = db.execute(query).scalars().all()
    assert circuit in rows
    for row in rows:
        assert not row.authorized_public
        assert row.authorized_project_id in user_context_user_1.user_project_ids
