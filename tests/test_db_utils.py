import uuid

import pytest
import sqlalchemy as sa

from app.db import model, utils as test_module
from app.db.model import User
from app.queries.utils import get_or_create_user, get_user
from app.schemas.auth import UserProfile


@pytest.mark.parametrize(
    ("cls", "parent_cls"),
    [
        (model.Species, None),
        (model.Entity, model.Entity),
        (model.Subject, model.Entity),
        (model.Circuit, model.Entity),
        (model.CellMorphology, model.Entity),
        (model.CellMorphologyProtocol, model.Entity),
        (model.ModifiedReconstructionCellMorphologyProtocol, model.Entity),
        (model.Activity, model.Activity),
        (model.SimulationExecution, model.Activity),
    ],
)
def test_authorized_project_id_declaring_class(cls, parent_cls):
    result_cls = test_module.get_authorized_project_id_declaring_class(cls)
    assert result_cls is parent_cls


def _profile(sub: uuid.UUID, name: str = "John Doe") -> UserProfile:
    return UserProfile(subject=sub, name=name, given_name="John", family_name="Doe")


def test_get_or_create_user__creates(db):
    sub = uuid.uuid4()
    user = get_or_create_user(db, _profile(sub, name="Jane Smith"))
    assert user.id == sub
    assert user.pref_label == "Jane Smith"
    assert user.given_name == "John"
    assert user.family_name == "Doe"
    assert db.get(User, sub) is not None


def test_get_or_create_user__idempotent(db):
    sub = uuid.uuid4()
    u1 = get_or_create_user(db, _profile(sub))
    u2 = get_or_create_user(db, _profile(sub))
    assert u1.id == u2.id
    count = db.execute(sa.select(sa.func.count()).select_from(User).where(User.id == sub)).scalar()
    assert count == 1


def test_get_user__found(db):
    sub = uuid.uuid4()
    get_or_create_user(db, _profile(sub))
    assert get_user(db, sub) is not None


def test_get_user__not_found(db):
    assert get_user(db, uuid.uuid4()) is None
