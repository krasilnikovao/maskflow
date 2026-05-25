from pathlib import Path

import pytest

from maskflow.runtime.paths import get_runtime_paths, resolve_data_path
from maskflow.runtime.settings import get_settings


def test_runtime_paths_use_maskflow_data_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_dir = tmp_path / "runtime-data"
    monkeypatch.setenv("MASKFLOW_DATA_DIR", str(data_dir))
    get_settings.cache_clear()

    try:
        paths = get_runtime_paths()

        assert paths.data_dir == data_dir
        assert paths.configs_dir == data_dir / "configs"
        assert paths.jobs_dir == data_dir / "jobs"
        assert paths.reports_dir == data_dir / "reports"
        assert paths.tmp_dir == data_dir / "tmp"
        assert paths.db_path == data_dir / "maskflow.sqlite"
    finally:
        get_settings.cache_clear()


def test_resolve_data_path_keeps_absolute_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_dir = tmp_path / "runtime-data"
    absolute_path = tmp_path / "cache.json"
    monkeypatch.setenv("MASKFLOW_DATA_DIR", str(data_dir))
    get_settings.cache_clear()

    try:
        assert resolve_data_path(absolute_path) == absolute_path
    finally:
        get_settings.cache_clear()


def test_resolve_data_path_places_relative_paths_under_data_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_dir = tmp_path / "runtime-data"
    monkeypatch.setenv("MASKFLOW_DATA_DIR", str(data_dir))
    get_settings.cache_clear()

    try:
        assert resolve_data_path("cache/entity-cache.json") == data_dir / "cache/entity-cache.json"
    finally:
        get_settings.cache_clear()
