from fastapi import APIRouter

import app.service.electrical_cell_recording

router = APIRouter(
    prefix="/electrical-cell-recording",
    tags=["electrical-cell-recording"],
)

read_many = router.get("")(app.service.electrical_cell_recording.read_many)
read_one = router.get("/{id_}")(app.service.electrical_cell_recording.read_one)
create_one = router.post("")(app.service.electrical_cell_recording.create_one)
update_one = router.patch("/{id_}")(app.service.electrical_cell_recording.update_one)
