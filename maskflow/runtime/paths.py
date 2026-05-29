from dataclasses import dataclass
from pathlib import Path

from maskflow.runtime.settings import MaskFlowSettings, get_settings


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    data_dir: Path
    configs_dir: Path
    jobs_dir: Path
    reports_dir: Path
    tmp_dir: Path
    db_path: Path
    # data/models/ - external spaCy model storage (mounted volume in Docker)
    models_dir: Path

    def ensure_directories(self) -> None:
        for path in (
            self.data_dir,
            self.configs_dir,
            self.jobs_dir,
            self.reports_dir,
            self.tmp_dir,
            # models_dir is created on demand by the NLP loader only,
            # so that running without NLP does not require the directory.
        ):
            path.mkdir(parents=True, exist_ok=True)

    def ensure_models_dir(self) -> Path:
        """Create data/models/ and return the path. Called only by the NLP loader."""
        self.models_dir.mkdir(parents=True, exist_ok=True)
        return self.models_dir


def get_runtime_paths(settings: MaskFlowSettings | None = None) -> RuntimePaths:
    resolved_settings = settings or get_settings()
    data_dir = resolved_settings.data_dir

    return RuntimePaths(
        data_dir=data_dir,
        configs_dir=data_dir / "configs",
        jobs_dir=data_dir / "jobs",
        reports_dir=data_dir / "reports",
        tmp_dir=data_dir / "tmp",
        db_path=data_dir / "maskflow.sqlite",
        models_dir=data_dir / "models",
    )


def resolve_data_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate

    return get_runtime_paths().data_dir / candidate
