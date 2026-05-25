from collections.abc import Iterable
from pathlib import Path

from maskflow.core.tasks import FileTask

SUPPORTED_EXTENSIONS = {
    ".txt",
    ".log",
    ".docx",
    ".xlsx",
    ".sql",
    ".csv",
    ".xml",
    ".json",
}


def build_directory_tasks(
    source_dir: Path,
    destination_dir: Path,
    config_path: Path,
    extensions: Iterable[str] = SUPPORTED_EXTENSIONS,
    overwrite: bool = False,
    timeout_seconds: int | None = None,
    plugins_dir: Path | None = None,
) -> list[FileTask]:
    if not source_dir.exists():
        raise FileNotFoundError(source_dir)

    if not source_dir.is_dir():
        raise ValueError(f"Source path is not a directory: {source_dir}")

    normalized_extensions = {extension.lower() for extension in extensions}

    tasks: list[FileTask] = []

    for source_file in source_dir.rglob("*"):
        if not source_file.is_file():
            continue

        if source_file.suffix.lower() not in normalized_extensions:
            continue

        relative_path = source_file.relative_to(source_dir)
        destination_file = destination_dir / relative_path

        tasks.append(
            FileTask(
                source=source_file,
                destination=destination_file,
                config_path=config_path,
                overwrite=overwrite,
                timeout_seconds=timeout_seconds,
                plugins_dir=plugins_dir,
            ),
        )

    return tasks
