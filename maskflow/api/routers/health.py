from fastapi import APIRouter, Depends

from maskflow.api.dependencies import runtime_paths_dependency
from maskflow.api.schemas import HealthResponse
from maskflow.runtime.paths import RuntimePaths

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(paths: RuntimePaths = Depends(runtime_paths_dependency)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        data_dir=paths.data_dir,
    )
