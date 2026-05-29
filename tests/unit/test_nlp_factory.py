from pathlib import Path

import pytest
from pytest import MonkeyPatch

from maskflow.nlp.factory import build_nlp_pipeline
from maskflow.nlp.providers.gliner import GlinerProvider
from maskflow.nlp.providers.natasha import NatashaProvider
from maskflow.nlp.providers.spacy import SpacyProvider
from maskflow.rules.models import (
    GlinerProviderConfig,
    NatashaProviderConfig,
    NlpConfig,
    NlpProvidersConfig,
    QwenProviderConfig,
    SpacyProviderConfig,
)
from maskflow.runtime.settings import get_settings


def test_build_nlp_pipeline_returns_none_when_disabled() -> None:
    assert build_nlp_pipeline(NlpConfig(enabled=False)) is None


def test_build_nlp_pipeline_rejects_enabled_config_without_providers() -> None:
    with pytest.raises(ValueError, match="no NLP providers are enabled"):
        build_nlp_pipeline(NlpConfig(enabled=True))


def test_build_nlp_pipeline_respects_provider_order(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("MASKFLOW_DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()

    try:
        monkeypatch.setattr(
            "maskflow.nlp.factory.ensure_model_available",
            lambda **kwargs: tmp_path / "data" / "models" / "gliner" / "model",
        )

        pipeline = build_nlp_pipeline(
            NlpConfig(
                enabled=True,
                min_confidence=0.6,
                provider_order=("natasha", "spacy", "gliner"),
                providers=NlpProvidersConfig(
                    gliner=GlinerProviderConfig(
                        enabled=True,
                        model_name="env/gliner",
                        model_path="gliner/model",
                        auto_download=None,
                        labels=("person", "organization"),
                        threshold=0.7,
                        batch_size=8,
                    ),
                    spacy=SpacyProviderConfig(
                        enabled=True,
                        model_name="ru_core_news_sm",
                        model_path="ru_core_news_md",
                        auto_download=False,
                        batch_size=16,
                    ),
                    natasha=NatashaProviderConfig(enabled=True),
                    qwen=QwenProviderConfig(enabled=False),
                ),
            )
        )
    finally:
        get_settings.cache_clear()

    assert pipeline is not None
    assert [provider.name for provider in pipeline.providers] == [
        "natasha",
        "spacy",
        "gliner",
    ]
    assert pipeline.resolver.min_confidence == 0.6

    natasha_provider = pipeline.providers[0]
    spacy_provider = pipeline.providers[1]
    gliner_provider = pipeline.providers[2]

    assert isinstance(natasha_provider, NatashaProvider)
    assert isinstance(spacy_provider, SpacyProvider)
    assert spacy_provider.model_name == "ru_core_news_sm"
    assert spacy_provider.model_path == "ru_core_news_md"
    assert spacy_provider.auto_download is False
    assert spacy_provider.batch_size == 16

    assert isinstance(gliner_provider, GlinerProvider)
    assert gliner_provider.model_name == "env/gliner"
    assert gliner_provider.model_path == (
        tmp_path / "data" / "models" / "gliner" / "model"
    )
    assert gliner_provider.auto_download is False
    assert gliner_provider.labels == ("person", "organization")
    assert gliner_provider.threshold == 0.7
    assert gliner_provider.batch_size == 8
