from pathlib import Path

from maskflow.runtime.paths import get_runtime_paths


def resolve_model_path(model_path: str | Path) -> Path:
    """Resolve absolute model paths or paths relative to data/models."""
    candidate = Path(model_path)
    if candidate.is_absolute():
        return candidate

    return get_runtime_paths().models_dir / candidate
