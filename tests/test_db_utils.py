import pytest

from app.db import model, utils as test_module


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
