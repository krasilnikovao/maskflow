from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileTask:
    source: Path
    destination: Path
    config_path: Path
    overwrite: bool = False
    timeout_seconds: int | None = None
    plugins_dir: Path | None = None


@dataclass(frozen=True, slots=True)
class FileResult:
    source: Path
    destination: Path
    success: bool
    message: str
