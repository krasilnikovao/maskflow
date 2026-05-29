from pathlib import Path
from typing import Literal, cast

import typer

from maskflow.cli.help import LocalizedTyperCommand
from maskflow.nlp.download import ensure_model_available
from maskflow.nlp.paths import resolve_model_path
from maskflow.rules.loader import RulesLoader
from maskflow.rules.models import NlpConfig
from maskflow.runtime.settings import get_settings

ModelProviderName = Literal["gliner", "qwen"]


def register_model_commands(app: typer.Typer) -> None:
    @app.command(
        "prepare-models",
        cls=LocalizedTyperCommand,
        help="Prepare configured NLP models under data/models.",
    )
    def prepare_models(
        config: Path = typer.Option(
            get_settings().default_config,
            "--config",
            "-c",
            help="Path to YAML config.",
        ),
        providers: list[str] | None = typer.Option(
            None,
            "--provider",
            "-p",
            help="Model provider to prepare. Repeatable: gliner, qwen.",
        ),
        auto_download: bool = typer.Option(
            False,
            "--auto-download",
            help="Allow model download even if YAML auto_download is false.",
        ),
    ) -> None:
        loaded_config = RulesLoader.load(config, validate_secret=False)
        selected_providers = _select_providers(
            loaded_config.nlp,
            _normalize_providers(providers),
        )

        if not selected_providers:
            typer.echo("No model providers selected.")
            return

        for provider in selected_providers:
            try:
                model_path = _prepare_provider(
                    provider=provider,
                    auto_download_override=auto_download,
                    config=loaded_config.nlp,
                )
            except (FileNotFoundError, RuntimeError) as error:
                raise typer.BadParameter(str(error)) from error

            typer.echo(f"{provider}: {model_path}")


def _select_providers(
    nlp_config: NlpConfig,
    providers: list[ModelProviderName] | None,
) -> list[ModelProviderName]:
    if providers:
        return providers

    selected: list[ModelProviderName] = []
    if nlp_config.providers.gliner.enabled:
        selected.append("gliner")
    if nlp_config.providers.qwen.enabled:
        selected.append("qwen")
    return selected


def _normalize_providers(providers: list[str] | None) -> list[ModelProviderName] | None:
    if providers is None:
        return None

    normalized: list[ModelProviderName] = []
    for provider in providers:
        if provider not in {"gliner", "qwen"}:
            raise typer.BadParameter("Provider must be one of: gliner, qwen")
        normalized.append(cast(ModelProviderName, provider))

    return normalized


def _prepare_provider(
    *,
    provider: ModelProviderName,
    auto_download_override: bool,
    config: NlpConfig,
) -> Path:
    if provider == "gliner":
        gliner_config = config.providers.gliner
        return ensure_model_available(
            provider="huggingface",
            model_name=gliner_config.model_name,
            model_path=(
                resolve_model_path(gliner_config.model_path)
                if gliner_config.model_path is not None
                else None
            ),
            auto_download=(
                auto_download_override
                or _effective_auto_download(
                    config.auto_download,
                    gliner_config.auto_download,
                )
            ),
        )

    qwen_config = config.providers.qwen
    return ensure_model_available(
        provider="huggingface",
        model_name=qwen_config.model_name,
        model_path=(
            resolve_model_path(qwen_config.model_path)
            if qwen_config.model_path is not None
            else None
        ),
        auto_download=(
            auto_download_override
            or _effective_auto_download(
                config.auto_download,
                qwen_config.auto_download,
            )
        ),
    )


def _effective_auto_download(
    global_auto_download: bool,
    provider_auto_download: bool | None,
) -> bool:
    if provider_auto_download is None:
        return global_auto_download
    return provider_auto_download
