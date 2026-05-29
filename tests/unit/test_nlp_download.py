import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pytest import MonkeyPatch

from maskflow.nlp import download as download_module
from maskflow.nlp.download import SpacyDownloader, ensure_model_available
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


def test_spacy_downloader_copies_installed_pipeline(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    package_path = tmp_path / "site-packages" / "ru_core_news_lg"
    pipeline_path = package_path / "ru_core_news_lg-3.8.0"
    pipeline_path.mkdir(parents=True)
    (pipeline_path / "config.cfg").write_text("[nlp]\n", encoding="utf-8")
    (pipeline_path / "meta.json").write_text("{}", encoding="utf-8")
    (pipeline_path / "tokenizer").write_text("data", encoding="utf-8")

    fake_spacy_util = SimpleNamespace(get_package_path=lambda _name: package_path)
    monkeypatch.setattr(
        download_module,
        "import_module",
        lambda name: fake_spacy_util if name == "spacy.util" else None,
    )

    destination = tmp_path / "data" / "models" / "spacy" / "ru_core_news_lg"
    destination.mkdir(parents=True)

    SpacyDownloader().download("ru_core_news_lg", destination)

    assert (destination / "config.cfg").read_text(encoding="utf-8") == "[nlp]\n"
    assert (destination / "meta.json").read_text(encoding="utf-8") == "{}"
    assert (destination / "tokenizer").read_text(encoding="utf-8") == "data"


def test_spacy_downloader_downloads_pipeline_to_destination(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    calls: list[tuple[Any, ...]] = []

    def fake_get_package_path(_name: str) -> Path:
        raise ModuleNotFoundError

    def fake_download(*args: Any) -> None:
        calls.append(args)
        target = Path(args[-1])
        pipeline_path = target / "ru_core_news_lg" / "ru_core_news_lg-3.8.0"
        pipeline_path.mkdir(parents=True)
        (pipeline_path / "config.cfg").write_text("[nlp]\n", encoding="utf-8")
        (pipeline_path / "meta.json").write_text("{}", encoding="utf-8")

    fake_spacy_util = SimpleNamespace(get_package_path=fake_get_package_path)
    fake_download_module = SimpleNamespace(download=fake_download)

    def fake_import_module(name: str) -> object:
        if name == "spacy.util":
            return fake_spacy_util
        if name == "spacy.cli.download":
            return fake_download_module
        raise ImportError(name)

    monkeypatch.setattr(download_module, "import_module", fake_import_module)

    destination = tmp_path / "data" / "models" / "spacy" / "ru_core_news_lg"
    destination.mkdir(parents=True)

    SpacyDownloader().download("ru_core_news_lg", destination)

    assert calls
    assert "--target" in calls[0]
    assert (destination / "config.cfg").is_file()
    assert (destination / "meta.json").is_file()
    assert not (destination / "_install").exists()
