from fastapi import APIRouter

import app.service.calibration_result

router = APIRouter(
    prefix="/calibration-result",
    tags=["calibration-result"],
)

read_many = router.get("")(app.service.calibration_result.read_many)
read_one = router.get("/{id_}")(app.service.calibration_result.read_one)
create_one = router.post("")(app.service.calibration_result.create_one)
