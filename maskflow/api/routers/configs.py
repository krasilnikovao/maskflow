from pathlib import Path

from fastapi import APIRouter, Depends

from maskflow.api.dependencies import runtime_paths_dependency, settings_dependency
from maskflow.api.schemas import ConfigInfo
from maskflow.runtime.paths import RuntimePaths
from maskflow.runtime.settings import MaskFlowSettings

router = APIRouter(prefix="/configs", tags=["configs"])


@router.get("", response_model=list[ConfigInfo])
def list_configs(
    paths: RuntimePaths = Depends(runtime_paths_dependency),
    settings: MaskFlowSettings = Depends(settings_dependency),
) -> list[ConfigInfo]:
    config_paths: dict[Path, ConfigInfo] = {}

    for path in (settings.default_config, *paths.configs_dir.glob("*.yaml")):
        if path.exists() and path.is_file():
            resolved = path.resolve()
            config_paths[resolved] = ConfigInfo(
                name=path.name,
                path=resolved,
            )

    return sorted(config_paths.values(), key=lambda item: item.name)
