from maskflow.runtime.paths import RuntimePaths, get_runtime_paths
from maskflow.runtime.settings import MaskFlowSettings, get_settings


def settings_dependency() -> MaskFlowSettings:
    return get_settings()


def runtime_paths_dependency() -> RuntimePaths:
    paths = get_runtime_paths()
    paths.ensure_directories()
    return paths
