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
