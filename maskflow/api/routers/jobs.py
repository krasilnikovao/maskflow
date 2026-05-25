from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from maskflow.api.dependencies import settings_dependency
from maskflow.api.schemas import (
    DemaskFileResponse,
    DemaskTextRequest,
    DemaskTextResponse,
    MaskFileResponse,
    MaskTextRequest,
    MaskTextResponse,
)
from maskflow.runtime.settings import MaskFlowSettings
from maskflow.services.demasking import DemaskingService
from maskflow.services.file_jobs import FileMaskingJobService
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


@router.post("/mask-file", response_model=MaskFileResponse)
def mask_file(
    file: UploadFile = File(...),
    config_path: Path | None = Form(None),
    settings: MaskFlowSettings = Depends(settings_dependency),
) -> MaskFileResponse:
    service = FileMaskingJobService()

    try:
        source_path = service.save_upload(
            filename=file.filename or "",
            stream=file.file,
        )
        result = service.process_file(
            source_path=source_path,
            original_name=file.filename or "",
            config_path=config_path or Path(settings.default_config),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    output_name = result.output_path.name

    return MaskFileResponse(
        job_id=result.job_id,
        original_name=result.original_name,
        output_name=output_name,
        matches_found=result.report.matches_found,
        matches_applied=result.report.matches_applied,
        matches_skipped=result.report.matches_skipped,
        download_url=f"/downloads/jobs/{result.job_id}/{output_name}",
        report_url=f"/downloads/reports/{result.report_path.name}",
    )


@router.post("/demask-text", response_model=DemaskTextResponse)
def demask_text(
    request: DemaskTextRequest,
    settings: MaskFlowSettings = Depends(settings_dependency),
) -> DemaskTextResponse:
    try:
        demasked_text, result = DemaskingService().demask_text(
            text=request.text,
            config_path=request.config_path or Path(settings.default_config),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return DemaskTextResponse(
        demasked_text=demasked_text,
        replacements=result.replacements,
        mapping_size=result.mapping_size,
    )


@router.post("/demask-file", response_model=DemaskFileResponse)
def demask_file(
    file: UploadFile = File(...),
    config_path: Path | None = Form(None),
    settings: MaskFlowSettings = Depends(settings_dependency),
) -> DemaskFileResponse:
    service = FileMaskingJobService()

    try:
        source_path = service.save_upload(
            filename=file.filename or "",
            stream=file.file,
        )
        result = service.demask_file(
            source_path=source_path,
            original_name=file.filename or "",
            config_path=config_path or Path(settings.default_config),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    output_name = result.output_path.name

    return DemaskFileResponse(
        job_id=result.job_id,
        original_name=result.original_name,
        output_name=output_name,
        replacements=result.replacements,
        mapping_size=result.mapping_size,
        download_url=f"/downloads/jobs/{result.job_id}/{output_name}",
    )
