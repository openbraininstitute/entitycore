from fastapi import APIRouter

import app.service.em_dense_reconstruction_dataset

router = APIRouter(
    prefix="/em-dense-reconstruction-dataset",
    tags=["em-dense-reconstruction-dataset"],
)

read_many = router.get("")(app.service.em_dense_reconstruction_dataset.read_many)
read_one = router.get("/{id_}")(app.service.em_dense_reconstruction_dataset.read_one)
create_one = router.post("")(app.service.em_dense_reconstruction_dataset.create_one)
