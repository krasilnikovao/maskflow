"""Загрузчик внешних плагинов.

ВНИМАНИЕ: ``load_external_plugins`` выполняет произвольный Python-код из
указанного каталога. Используйте ТОЛЬКО доверенные каталоги. Для production
рекомендуется хранить SHA-256 хеши и сверять их через ``trusted_hashes``.
"""

import hashlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from maskflow.plugins.registry import PluginRegistry
from maskflow.utils.logging import get_logger

logger = get_logger("maskflow.plugins")


@dataclass(frozen=True, slots=True)
class PluginLoadError:
    plugin_path: Path
    message: str


@dataclass(frozen=True, slots=True)
class PluginLoadResult:
    loaded: int
    failed: int
    errors: list[PluginLoadError]


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_external_plugins(
    registry: PluginRegistry,
    plugins_dir: Path,
    strict: bool = True,
    trusted_hashes: set[str] | None = None,
) -> PluginLoadResult:
    """Загружает плагины из каталога.

    Если ``trusted_hashes`` задан — отказывает в загрузке плагинам,
    SHA-256 которых не входит в список.
    """
    if not plugins_dir.exists():
        return PluginLoadResult(loaded=0, failed=0, errors=[])

    if not plugins_dir.is_dir():
        raise ValueError(f"Plugins path is not a directory: {plugins_dir}")

    logger.warning(
        "external_plugins_loading",
        plugins_dir=str(plugins_dir),
        note="external plugins execute arbitrary Python code",
    )

    if trusted_hashes is None:
        logger.warning(
            "external_plugins_no_hash_verification",
            plugins_dir=str(plugins_dir),
            note=(
                "trusted_hashes not provided — plugin integrity is NOT verified. "
                "Pass trusted_hashes=set_of_sha256 to enforce allowlist."
            ),
        )

    loaded = 0
    errors: list[PluginLoadError] = []

    for plugin_file in sorted(plugins_dir.glob("*.py")):
        if plugin_file.name.startswith("_"):
            continue

        try:
            if trusted_hashes is not None:
                file_hash = _file_sha256(plugin_file)
                if file_hash not in trusted_hashes:
                    raise ValueError(
                        f"Plugin hash {file_hash} is not in trusted_hashes"
                    )

            module = _load_plugin_module(plugin_file)
            register_plugins = getattr(module, "register_plugins", None)

            if register_plugins is None:
                raise ValueError("Plugin has no register_plugins function")

            register_plugins(registry)
            loaded += 1

        except Exception as error:
            plugin_error = PluginLoadError(
                plugin_path=plugin_file,
                message=f"{type(error).__name__}: {error}",
            )

            if strict:
                raise ValueError(
                    f"Failed to load plugin {plugin_file}: {type(error).__name__}: {error}"
                ) from error

            logger.error(
                "plugin_load_failed",
                plugin_path=str(plugin_file),
                error=plugin_error.message,
            )
            errors.append(plugin_error)

    return PluginLoadResult(
        loaded=loaded,
        failed=len(errors),
        errors=errors,
    )


def _load_plugin_module(plugin_file: Path) -> ModuleType:
    module_name = f"maskflow_external_plugin_{plugin_file.stem}"

    spec = importlib.util.spec_from_file_location(
        module_name,
        plugin_file,
    )

    if spec is None or spec.loader is None:
        raise ValueError(f"Unable to load plugin: {plugin_file}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module
