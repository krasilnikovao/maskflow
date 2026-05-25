from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from maskflow.api.dependencies import runtime_paths_dependency
from maskflow.runtime.paths import RuntimePaths
from maskflow.runtime.permissions import assert_child_path

router = APIRouter(prefix="/downloads", tags=["downloads"])


@router.get("/reports/{name}")
def download_report(
    name: str,
    paths: RuntimePaths = Depends(runtime_paths_dependency),
) -> FileResponse:
    try:
        report_path = assert_child_path(paths.reports_dir, name)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if not report_path.exists() or not report_path.is_file():
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(report_path)


@router.get("/jobs/{job_id}/{name}")
def download_job_file(
    job_id: str,
    name: str,
    paths: RuntimePaths = Depends(runtime_paths_dependency),
) -> FileResponse:
    try:
        job_dir = assert_child_path(paths.jobs_dir, job_id)
        output_dir = assert_child_path(job_dir, "output")
        output_path = assert_child_path(output_dir, name)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if not output_path.exists() or not output_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        output_path,
        filename=output_path.name,
    )
