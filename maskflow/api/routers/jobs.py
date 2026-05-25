from pathlib import Path

from fastapi import APIRouter, Depends

from maskflow.api.dependencies import settings_dependency
from maskflow.api.schemas import MaskTextRequest, MaskTextResponse
from maskflow.runtime.settings import MaskFlowSettings
from maskflow.services.text_masking import TextMaskingService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/mask-text", response_model=MaskTextResponse)
def mask_text(
    request: MaskTextRequest,
    settings: MaskFlowSettings = Depends(settings_dependency),
) -> MaskTextResponse:
    service = TextMaskingService()
    result = service.mask_text(
        text=request.text,
        config_path=request.config_path or Path(settings.default_config),
        plugins_dir=request.plugins_dir,
    )

    return MaskTextResponse(
        masked_text=result.masked_text,
        matches_found=result.matches_found,
        matches_applied=result.matches_applied,
        matches_skipped=result.matches_skipped,
        detector_counts=result.detector_counts,
        detector_timings_ms=result.detector_timings_ms,
    )
