from pathlib import Path
from typing import Any, cast

import pytest

from maskflow.runtime.paths import get_runtime_paths, resolve_data_path
from maskflow.runtime.settings import MaskFlowSettings, get_settings


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
        assert resolve_data_path("cache/entity-cache.json") == (
            data_dir / "cache/entity-cache.json"
        )
    finally:
        get_settings.cache_clear()


def test_runtime_settings_load_nlp_model_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MASKFLOW_NLP_ENABLED", "true")
    monkeypatch.setenv("MASKFLOW_NLP_AUTO_DOWNLOAD", "true")
    monkeypatch.setenv("MASKFLOW_GLINER_ENABLED", "true")
    monkeypatch.setenv("MASKFLOW_GLINER_MODEL", "env/gliner")
    monkeypatch.setenv("MASKFLOW_GLINER_MODEL_PATH", "gliner/env")
    monkeypatch.setenv("MASKFLOW_GLINER_DEVICE", "cuda:0")
    monkeypatch.setenv("MASKFLOW_SPACY_ENABLED", "true")
    monkeypatch.setenv("MASKFLOW_SPACY_MODEL", "ru_core_news_sm")
    monkeypatch.setenv("MASKFLOW_SPACY_MODEL_PATH", "spacy/env")
    monkeypatch.setenv("MASKFLOW_NATASHA_ENABLED", "true")
    monkeypatch.setenv("MASKFLOW_QWEN_ENABLED", "true")
    monkeypatch.setenv("MASKFLOW_QWEN_MODEL", "Qwen/example")
    monkeypatch.setenv("MASKFLOW_QWEN_MODEL_PATH", "qwen/env")
    monkeypatch.setenv("MASKFLOW_QWEN_DEVICE", "cuda:1")

    settings = MaskFlowSettings()

    assert settings.nlp_enabled is True
    assert settings.nlp_auto_download is True
    assert settings.gliner_enabled is True
    assert settings.gliner_model == "env/gliner"
    assert settings.gliner_model_path == "gliner/env"
    assert settings.gliner_device == "cuda:0"
    assert settings.spacy_enabled is True
    assert settings.spacy_model == "ru_core_news_sm"
    assert settings.spacy_model_path == "spacy/env"
    assert settings.natasha_enabled is True
    assert settings.qwen_enabled is True
    assert settings.qwen_model == "Qwen/example"
    assert settings.qwen_model_path == "qwen/env"
    assert settings.qwen_device == "cuda:1"


def test_runtime_settings_normalizes_relative_default_config_path() -> None:
    settings = MaskFlowSettings(
        default_config=cast(Any, "configs\\examples\\nlp.yaml"),
    )

    assert settings.default_config == Path("configs/examples/nlp.yaml")
