from pathlib import Path

from pytest import MonkeyPatch

from maskflow.nlp.paths import resolve_model_path
from maskflow.runtime.settings import get_settings


def test_resolve_model_path_keeps_absolute_path(tmp_path: Path) -> None:
    model_path = tmp_path / "model"

    assert resolve_model_path(model_path) == model_path


def test_resolve_model_path_uses_data_models_dir(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("MASKFLOW_DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()

    try:
        assert resolve_model_path("gliner/model") == (
            tmp_path / "data" / "models" / "gliner" / "model"
        )
    finally:
        get_settings.cache_clear()
