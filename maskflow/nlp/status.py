from dataclasses import dataclass
from pathlib import Path

from maskflow.nlp.download import default_model_path, is_model_available
from maskflow.nlp.paths import resolve_model_path
from maskflow.rules.models import NlpConfig


@dataclass(frozen=True, slots=True)
class NlpModelStatus:
    provider: str
    enabled: bool
    model_name: str
    model_path: Path
    available: bool
    auto_download: bool


def collect_nlp_model_status(config: NlpConfig) -> list[NlpModelStatus]:
    return [
        _gliner_status(config),
        _spacy_status(config),
        _qwen_status(config),
    ]


def _gliner_status(config: NlpConfig) -> NlpModelStatus:
    provider_config = config.providers.gliner
    model_path = (
        resolve_model_path(provider_config.model_path)
        if provider_config.model_path is not None
        else default_model_path("huggingface", provider_config.model_name)
    )
    return NlpModelStatus(
        provider="gliner",
        enabled=provider_config.enabled,
        model_name=provider_config.model_name,
        model_path=model_path,
        available=is_model_available(model_path, provider="huggingface"),
        auto_download=_effective_auto_download(
            config.auto_download,
            provider_config.auto_download,
        ),
    )


def _spacy_status(config: NlpConfig) -> NlpModelStatus:
    provider_config = config.providers.spacy
    model_path = (
        resolve_model_path(provider_config.model_path)
        if provider_config.model_path is not None
        else default_model_path("spacy", provider_config.model_name)
    )
    return NlpModelStatus(
        provider="spacy",
        enabled=provider_config.enabled,
        model_name=provider_config.model_name,
        model_path=model_path,
        available=is_model_available(model_path, provider="spacy"),
        auto_download=_effective_auto_download(
            config.auto_download,
            provider_config.auto_download,
        ),
    )


def _qwen_status(config: NlpConfig) -> NlpModelStatus:
    provider_config = config.providers.qwen
    model_path = (
        resolve_model_path(provider_config.model_path)
        if provider_config.model_path is not None
        else default_model_path("huggingface", provider_config.model_name)
    )
    return NlpModelStatus(
        provider="qwen",
        enabled=provider_config.enabled,
        model_name=provider_config.model_name,
        model_path=model_path,
        available=is_model_available(model_path, provider="huggingface"),
        auto_download=_effective_auto_download(
            config.auto_download,
            provider_config.auto_download,
        ),
    )


def _effective_auto_download(
    global_auto_download: bool,
    provider_auto_download: bool | None,
) -> bool:
    if provider_auto_download is None:
        return global_auto_download
    return provider_auto_download
