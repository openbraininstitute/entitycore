from fastapi import APIRouter

import app.service.experimental_bouton_density

router = APIRouter(
    prefix="/experimental-bouton-density",
    tags=["experimental-bouton-density"],
)

read_many = router.get("")(app.service.experimental_bouton_density.read_many)
read_onw = router.get("/{id_}")(app.service.experimental_bouton_density.read_one)
create = router.post("")(app.service.experimental_bouton_density.create)
