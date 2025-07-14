from app.db import utils as test_module
from app.db.model import MeasurementAnnotation, MeasurementKind, CellMorphology
from app.schemas.measurement_annotation import MeasurementAnnotationCreate
from app.schemas.morphology import CellMorphologyCreate

from tests.utils import PROJECT_ID

ENTITY_TYPE = "reconstruction_morphology"
ENTITY_ID = "2013824a-ad49-4179-a961-8e7a98deb9d0"
SPECIES_ID = "6de20568-8e44-4341-ad5a-8999d2d23de2"

MEASUREMENT_ANNOTATION = {
    "unknown_attribute": 999999,
    "entity_type": ENTITY_TYPE,
    "entity_id": ENTITY_ID,
    "measurement_kinds": [
        {
            "pref_label": "pref_label_0",
            "structural_domain": "axon",
            "measurement_items": [
                {
                    "name": "mean",
                    "unit": "μm",
                    "value": 54.2,
                },
                {
                    "name": "median",
                    "unit": "μm",
                    "value": 44.6,
                },
            ],
        },
        {
            "pref_label": "pref_label_1",
            "structural_domain": "soma",
            "measurement_items": [
                {
                    "name": "mean",
                    "unit": "μm²",
                    "value": 97.6,
                },
                {
                    "name": "median",
                    "unit": "μm²",
                    "value": 73.86,
                },
            ],
        },
    ],
}


def test_construct_model_measurement_annotation(person_id):
    def _check_result(r):
        assert isinstance(r, MeasurementAnnotation)
        assert str(r.entity_id) == MEASUREMENT_ANNOTATION["entity_id"]
        assert len(r.measurement_kinds) == 2
        assert isinstance(r.measurement_kinds[0], MeasurementKind)
        assert isinstance(r.measurement_kinds[1], MeasurementKind)

    result = test_module.construct_model(
        model_cls=MeasurementAnnotation, data=MEASUREMENT_ANNOTATION
    )
    _check_result(result)

    json_model = MeasurementAnnotationCreate.model_validate(MEASUREMENT_ANNOTATION)
    result = test_module.load_db_model_from_pydantic(
        json_model,
        db_model_class=MeasurementAnnotation,
        authorized_project_id=None,
        created_by_id=person_id,
        updated_by_id=person_id,
    )
    _check_result(result)


def test_construct_model_reconstruction_morphology(brain_region_id, person_id):
    reconstruction_morphology = {
        "name": "morph-0",
        "description": "desc-0",
        "species_id": SPECIES_ID,
        "brain_region_id": str(brain_region_id),
        "location": {"x": 100.1, "y": 100.2, "z": 100.3},
    }

    def _check_result(r):
        assert isinstance(r, CellMorphology)
        assert r.name == reconstruction_morphology["name"]
        assert r.location == reconstruction_morphology["location"]

    result = test_module.construct_model(model_cls=CellMorphology, data=reconstruction_morphology)
    _check_result(result)

    json_model = CellMorphologyCreate.model_validate(reconstruction_morphology)
    result = test_module.load_db_model_from_pydantic(
        json_model,
        db_model_class=CellMorphology,
        authorized_project_id=PROJECT_ID,
        created_by_id=person_id,
        updated_by_id=person_id,
    )
    _check_result(result)
