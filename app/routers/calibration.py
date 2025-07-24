from fastapi import APIRouter

import app.service.calibration

router = APIRouter(
    prefix="/calibration",
    tags=["calibration"],
)

read_many = router.get("")(app.service.calibration.read_many)
read_one = router.get("/{id_}")(app.service.calibration.read_one)
create_one = router.post("")(app.service.calibration.create_one)
delete_one = router.delete("/{id_}")(app.service.calibration.delete_one)
update_one = router.patch("/{id_}")(app.service.calibration.update_one)
