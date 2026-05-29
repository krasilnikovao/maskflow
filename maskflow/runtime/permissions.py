import os
from pathlib import Path

from maskflow.runtime.paths import RuntimePaths, get_runtime_paths


def ensure_runtime_permissions(paths: RuntimePaths | None = None) -> None:
    runtime_paths = paths or get_runtime_paths()
    runtime_paths.ensure_directories()

    if os.name == "nt":
        return

    for path in (
        runtime_paths.data_dir,
        runtime_paths.configs_dir,
        runtime_paths.jobs_dir,
        runtime_paths.reports_dir,
        runtime_paths.tmp_dir,
    ):
        path.chmod(0o700)


def assert_child_path(parent: Path, child_name: str) -> Path:
    parent_resolved = parent.resolve()
    child = (parent / child_name).resolve()

    if parent_resolved != child and parent_resolved not in child.parents:
        raise ValueError(f"Path escapes runtime directory: {child_name}")

    return child
