from fastapi import APIRouter

from app.service import analysis_notebook_environment as service

router = APIRouter(
    prefix="/analysis-notebook-environment",
    tags=["analysis-notebook-environment"],
)

read_many = router.get("")(service.read_many)
read_one = router.get("/{id_}")(service.read_one)
create_one = router.post("")(service.create_one)
delete_one = router.delete("/{id_}")(service.delete_one)
update_one = router.patch("/{id_}")(service.update_one)
