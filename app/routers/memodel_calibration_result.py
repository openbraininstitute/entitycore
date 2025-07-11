from fastapi import APIRouter

import app.service.memodel_calibration_result

router = APIRouter(
    prefix="/memodel-calibration-result",
    tags=["memodel-calibration-result"],
)
read_many = router.get("")(app.service.memodel_calibration_result.read_many)
read_one = router.get("/{id_}")(app.service.memodel_calibration_result.read_one)
create_one = router.post("")(app.service.memodel_calibration_result.create_one)
delete_one = router.delete("/{id_}")(app.service.memodel_calibration_result.delete_one)
