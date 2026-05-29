import json
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from maskflow.nlp.download import ensure_model_available
from maskflow.runtime.settings import get_settings


class FakeDownloader:
    def download(self, model_name: str, destination: Path) -> None:
        (destination / "model.bin").write_text(model_name, encoding="utf-8")


def test_ensure_model_available_returns_existing_model(tmp_path: Path) -> None:
    model_path = tmp_path / "model"
    model_path.mkdir()
    (model_path / "config.json").write_text("{}", encoding="utf-8")

    result = ensure_model_available(
        provider="huggingface",
        model_name="example/model",
        model_path=model_path,
        auto_download=False,
    )

    assert result == model_path


def test_ensure_model_available_rejects_missing_model_without_download(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError, match="enable nlp.auto_download"):
        ensure_model_available(
            provider="huggingface",
            model_name="example/model",
            model_path=tmp_path / "missing",
            auto_download=False,
        )


def test_ensure_model_available_downloads_to_data_models(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("MASKFLOW_DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()

    try:
        result = ensure_model_available(
            provider="huggingface",
            model_name="example/model",
            model_path=None,
            auto_download=True,
            downloader=FakeDownloader(),
        )
    finally:
        get_settings.cache_clear()

    assert result == (
        tmp_path / "data" / "models" / "huggingface" / "example__model"
    )
    assert (result / "model.bin").read_text(encoding="utf-8") == "example/model"

    manifest = json.loads((result / "maskflow-model.json").read_text(encoding="utf-8"))
    assert manifest["provider"] == "huggingface"
    assert manifest["model_name"] == "example/model"
