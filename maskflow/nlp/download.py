import json
import shutil
from dataclasses import asdict, dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Literal, Protocol, cast

from maskflow.runtime.paths import get_runtime_paths
from maskflow.utils.atomic import atomic_write_text
from maskflow.utils.filelock import file_lock

ModelProvider = Literal["huggingface", "spacy"]

_MANIFEST_NAME = "maskflow-model.json"


@dataclass(frozen=True, slots=True)
class ModelManifest:
    provider: ModelProvider
    model_name: str
    model_path: Path


class ModelDownloader(Protocol):
    def download(self, model_name: str, destination: Path) -> None:
        raise NotImplementedError


def ensure_model_available(
    *,
    provider: ModelProvider,
    model_name: str,
    model_path: Path | None,
    auto_download: bool,
    downloader: ModelDownloader | None = None,
) -> Path:
    destination = (
        default_model_path(provider, model_name)
        if model_path is None
        else model_path
    )

    if is_model_available(destination):
        return destination

    if not auto_download:
        raise FileNotFoundError(
            f"NLP model is not available locally: {destination}. "
            "Place the model under data/models or enable nlp.auto_download."
        )

    lock_path = destination.with_suffix(destination.suffix + ".lock")
    with file_lock(lock_path):
        if is_model_available(destination):
            return destination

        temp_destination = destination.with_name(f".{destination.name}.download")
        if temp_destination.exists():
            shutil.rmtree(temp_destination)

        temp_destination.mkdir(parents=True, exist_ok=True)
        _select_downloader(provider, downloader).download(model_name, temp_destination)
        _write_manifest(
            temp_destination,
            ModelManifest(
                provider=provider,
                model_name=model_name,
                model_path=destination,
            ),
        )

        if destination.exists():
            shutil.rmtree(destination)
        temp_destination.replace(destination)

    return destination


def default_model_path(provider: ModelProvider, model_name: str) -> Path:
    safe_model_name = model_name.replace("/", "__")
    return get_runtime_paths().models_dir / provider / safe_model_name


def is_model_available(path: Path) -> bool:
    return path.exists() and path.is_dir() and any(path.iterdir())


def _select_downloader(
    provider: ModelProvider,
    downloader: ModelDownloader | None,
) -> ModelDownloader:
    if downloader is not None:
        return downloader

    if provider == "huggingface":
        return HuggingFaceDownloader()
    return SpacyDownloader()


class HuggingFaceDownloader:
    def download(self, model_name: str, destination: Path) -> None:
        try:
            huggingface_hub = import_module("huggingface_hub")
        except ImportError as error:
            raise RuntimeError(
                "huggingface_hub is required for Hugging Face model download"
            ) from error

        snapshot_download = cast(Any, huggingface_hub).snapshot_download
        snapshot_download(
            repo_id=model_name,
            local_dir=destination,
            local_dir_use_symlinks=False,
        )


class SpacyDownloader:
    def download(self, model_name: str, destination: Path) -> None:
        try:
            spacy_cli = import_module("spacy.cli")
        except ImportError as error:
            raise RuntimeError("spaCy is required for spaCy model download") from error

        spacy_download = cast(Any, spacy_cli).download
        spacy_download(model_name)

        raise RuntimeError(
            "spaCy downloaded an installed package. Copying installed package models "
            "into data/models is not implemented yet."
        )


def _write_manifest(destination: Path, manifest: ModelManifest) -> None:
    payload = asdict(manifest)
    payload["model_path"] = str(manifest.model_path)
    atomic_write_text(
        destination=destination / _MANIFEST_NAME,
        content=json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
    )
