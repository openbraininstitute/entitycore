from pathlib import Path

from fastapi import APIRouter, Response

COMPOSITION_SUMMARY = (
    (Path(__file__).parent.parent / "static/cellCompositionSummary_payload_prod.json").open().read()
)


router = APIRouter(
    prefix="/cell-composition",
    tags=["/cell-composition"],
)


@router.get("/")
def get() -> Response:
    """Return the old style cellCompositionSummary_payload_prod.json."""
    response = Response(content=COMPOSITION_SUMMARY, media_type="application/json")
    return response
