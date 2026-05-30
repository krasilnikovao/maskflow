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

    if is_model_available(destination, provider=provider):
        return destination

    if not auto_download:
        raise FileNotFoundError(
            f"NLP model is not available locally: {destination}. "
            "Place the model under data/models or enable nlp.auto_download."
        )

    lock_path = destination.with_suffix(destination.suffix + ".lock")
    with file_lock(lock_path):
        if is_model_available(destination, provider=provider):
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


def is_model_available(path: Path, provider: ModelProvider | None = None) -> bool:
    if not path.exists() or not path.is_dir() or not any(path.iterdir()):
        return False

    if provider == "huggingface":
        return (path / "config.json").is_file() or (path / "gliner_config.json").is_file()

    if provider == "spacy":
        return _is_spacy_pipeline_dir(path)

    return True


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
        installed_pipeline = _find_installed_spacy_pipeline(model_name)
        if installed_pipeline is not None:
            _copy_spacy_pipeline(installed_pipeline, destination)
            return

        try:
            spacy_download_module = import_module("spacy.cli.download")
        except ImportError as error:
            raise RuntimeError("spaCy is required for spaCy model download") from error

        install_dir = destination / "_install"
        if install_dir.exists():
            shutil.rmtree(install_dir)
        install_dir.mkdir(parents=True, exist_ok=True)

        spacy_download = cast(Any, spacy_download_module).download
        spacy_download(
            model_name,
            False,
            False,
            None,
            "--no-deps",
            "--target",
            str(install_dir),
        )

        downloaded_pipeline = _find_spacy_pipeline_dir(install_dir)
        _copy_spacy_pipeline(downloaded_pipeline, destination)
        shutil.rmtree(install_dir)


def _write_manifest(destination: Path, manifest: ModelManifest) -> None:
    payload = asdict(manifest)
    payload["model_path"] = str(manifest.model_path)
    atomic_write_text(
        destination=destination / _MANIFEST_NAME,
        content=json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
    )


def _find_installed_spacy_pipeline(model_name: str) -> Path | None:
    try:
        spacy_util = import_module("spacy.util")
        package_path = cast(Any, spacy_util).get_package_path(model_name)
    except (ImportError, ModuleNotFoundError, OSError):
        return None

    try:
        return _find_spacy_pipeline_dir(Path(package_path))
    except RuntimeError:
        return None


def _find_spacy_pipeline_dir(root: Path) -> Path:
    if _is_spacy_pipeline_dir(root):
        return root

    for config_path in sorted(root.rglob("config.cfg")):
        candidate = config_path.parent
        if _is_spacy_pipeline_dir(candidate):
            return candidate

    raise RuntimeError(f"Downloaded spaCy model does not contain a pipeline: {root}")


def _is_spacy_pipeline_dir(path: Path) -> bool:
    return (path / "config.cfg").is_file() and (path / "meta.json").is_file()


def _copy_spacy_pipeline(source: Path, destination: Path) -> None:
    staging = destination / "_pipeline"
    if staging.exists():
        shutil.rmtree(staging)

    shutil.copytree(source, staging)
    for item in staging.iterdir():
        target = destination / item.name
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        shutil.move(str(item), target)

    shutil.rmtree(staging)
