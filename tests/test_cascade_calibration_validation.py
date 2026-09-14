"""Cascade deletion of calibration/validation results with memodel and emodel."""

import pytest
import sqlalchemy as sa

from app.db.model import (
    CellMorphology,
    EModel,
    Entity,
    MEModel,
    MEModelCalibrationResult,
    ValidationResult,
)

from .utils import assert_request, check_db_counts

MEMODEL = "/memodel"
EMODEL = "/emodel"
CALIBRATION = "/memodel-calibration-result"
VALIDATION = "/validation-result"


def _post_validation(client, entity_id, *, name="vr"):
    return assert_request(
        client.post,
        url=VALIDATION,
        json={
            "name": name,
            "passed": True,
            "validated_entity_id": str(entity_id),
            "authorized_public": False,
        },
    ).json()["id"]


def _post_calibration(client, memodel_id):
    return assert_request(
        client.post,
        url=CALIBRATION,
        json={
            "calibrated_entity_id": str(memodel_id),
            "authorized_public": False,
            "threshold_current": 0.8,
            "holding_current": 0.2,
            "rin": 100.0,
        },
    ).json()["id"]


def _admin_delete(clients, route, entity_id):
    assert_request(clients.admin.delete, url=f"/admin{route}/{entity_id}")


def _entity_exists(db, entity_id) -> bool:
    return (
        db.execute(
            sa.select(sa.func.count()).select_from(Entity).where(Entity.id == entity_id)
        ).scalar()
        == 1
    )


def _assert_gone_via_api(clients, route, entity_id):
    assert_request(clients.admin.get, url=f"/admin{route}/{entity_id}", expected_status_code=404)


@pytest.mark.parametrize(
    ("with_calibration", "n_validations"),
    [
        (False, 0),
        (True, 0),
        (False, 1),
        (True, 2),
    ],
    ids=["plain", "calibration", "validation", "calibration+validations"],
)
def test_memodel_delete_cascades(
    db, clients, client, memodel_id, morphology_id, with_calibration, n_validations
):
    cal_id = _post_calibration(client, memodel_id) if with_calibration else None
    vr_ids = [_post_validation(client, memodel_id, name=f"vr-{i}") for i in range(n_validations)]
    unrelated = _post_validation(client, morphology_id, name="unrelated")

    check_db_counts(
        db,
        {
            MEModel: 1,
            MEModelCalibrationResult: int(with_calibration),
            ValidationResult: n_validations + 1,
            EModel: 1,
            CellMorphology: 1,
        },
    )
    _admin_delete(clients, MEMODEL, memodel_id)
    check_db_counts(
        db,
        {
            MEModel: 0,
            MEModelCalibrationResult: 0,
            ValidationResult: 1,
            EModel: 1,
            CellMorphology: 1,
        },
    )

    assert not _entity_exists(db, memodel_id)
    if cal_id:
        # relationship cascade removes calibration child + entity row
        assert not _entity_exists(db, cal_id)
        _assert_gone_via_api(clients, CALIBRATION, cal_id)
    for vr_id in vr_ids:
        # FK CASCADE removes validation_result row (joined load 404s)
        _assert_gone_via_api(clients, VALIDATION, vr_id)
    assert_request(clients.admin.get, url=f"/admin{VALIDATION}/{unrelated}")


@pytest.mark.parametrize("n_validations", [0, 1, 2], ids=["plain", "validation", "validations"])
def test_emodel_delete_cascades(db, clients, client, emodel_id, morphology_id, n_validations):
    vr_ids = [_post_validation(client, emodel_id, name=f"vr-{i}") for i in range(n_validations)]
    unrelated = _post_validation(client, morphology_id, name="unrelated")

    check_db_counts(
        db,
        {
            EModel: 1,
            ValidationResult: n_validations + 1,
            CellMorphology: 1,
        },
    )
    _admin_delete(clients, EMODEL, emodel_id)
    check_db_counts(
        db,
        {
            EModel: 0,
            ValidationResult: 1,
            CellMorphology: 1,
        },
    )

    assert not _entity_exists(db, emodel_id)
    for vr_id in vr_ids:
        _assert_gone_via_api(clients, VALIDATION, vr_id)
    assert_request(clients.admin.get, url=f"/admin{VALIDATION}/{unrelated}")


def test_deleting_results_does_not_delete_parent(db, clients, client, memodel_id, emodel_id):
    cal_id = _post_calibration(client, memodel_id)
    memodel_vr = _post_validation(client, memodel_id, name="memodel-vr")
    emodel_vr = _post_validation(client, emodel_id, name="emodel-vr")

    _admin_delete(clients, CALIBRATION, cal_id)
    _admin_delete(clients, VALIDATION, memodel_vr)
    _admin_delete(clients, VALIDATION, emodel_vr)

    check_db_counts(
        db,
        {
            MEModel: 1,
            EModel: 1,
            MEModelCalibrationResult: 0,
            ValidationResult: 0,
        },
    )
    assert _entity_exists(db, memodel_id)
    assert _entity_exists(db, emodel_id)
