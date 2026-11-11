import uuid

import pytest
import sqlalchemy as sa

from app.db import model, utils as test_module
from app.db.model import Person, PlatformUser
from app.db.types import EntityType
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


def test_entity_type_to_class():
    assert set(test_module.ENTITY_TYPE_TO_CLASS) == set(EntityType)
    assert (
        test_module.ENTITY_TYPE_TO_CLASS[EntityType.cell_morphology_protocol]
        is model.CellMorphologyProtocol
    )
    for entity_type, cls in test_module.ENTITY_TYPE_TO_CLASS.items():
        assert cls.__tablename__ == entity_type
        assert not sa.inspect(cls).single


def _profile(sub: uuid.UUID, name: str = "John Doe") -> UserProfile:
    return UserProfile(subject=sub, name=name)


def test_get_or_create_user__creates(db):
    sub = uuid.uuid4()
    user = get_or_create_user(db, _profile(sub, name="Jane Smith"))
    assert user.id == sub
    assert user.pref_label == "Jane Smith"
    assert db.get(PlatformUser, sub) is not None

    # A Person is auto-created with matching sub_id
    person = db.execute(sa.select(Person).where(Person.sub_id == sub)).scalar_one_or_none()
    assert person is not None
    assert person.pref_label == "Jane Smith"
    assert person.created_by_id == sub
    assert person.updated_by_id == sub


def test_get_or_create_user__idempotent(db):
    sub = uuid.uuid4()
    u1 = get_or_create_user(db, _profile(sub))
    u2 = get_or_create_user(db, _profile(sub))
    assert u1.id == u2.id
    count = db.execute(
        sa.select(sa.func.count()).select_from(PlatformUser).where(PlatformUser.id == sub)
    ).scalar()
    assert count == 1

    # Only one Person was created
    person_count = db.execute(
        sa.select(sa.func.count()).select_from(Person).where(Person.sub_id == sub)
    ).scalar()
    assert person_count == 1


def test_get_user__found(db):
    sub = uuid.uuid4()
    get_or_create_user(db, _profile(sub))
    assert get_user(db, sub) is not None


def test_get_user__not_found(db):
    assert get_user(db, uuid.uuid4()) is None


@pytest.mark.parametrize(
    ("db_model_class", "expected"),
    [
        (model.Circuit, (EntityType.circuit,)),
        (model.CellMorphologyProtocol, (EntityType.cell_morphology_protocol,)),
        (
            model.ElectricalRecording,
            (
                EntityType.electrical_cell_recording,
                EntityType.electrical_recording,
                EntityType.ion_channel_recording,
            ),
        ),
        (model.ExternalUrl, (EntityType.external_url,)),
    ],
)
def test_get_entity_types(db_model_class, expected):
    assert test_module.get_entity_types(db_model_class) == expected


def test_get_entity_types_raises():
    with pytest.raises(TypeError, match="Strain is not an entity class"):
        test_module.get_entity_types(model.Strain)


@pytest.mark.usefixtures("morphology_id")
def test_get_entity_types_match_the_stored_types(db):
    for db_model_class in (model.CellMorphology, model.ScientificArtifact):
        stored = set(db.execute(sa.select(model.Entity.type).select_from(db_model_class)).scalars())
        assert stored
        assert stored <= set(test_module.get_entity_types(db_model_class))
