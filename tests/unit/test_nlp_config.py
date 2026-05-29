from pathlib import Path

import pytest

from maskflow.rules.loader import RulesLoader


def test_rules_loader_uses_default_disabled_nlp_config(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        """
pipeline:
  deterministic_secret: "secret"

rules:
  email:
    enabled: true
    mode: hmac
    prefix: EMAIL
""",
        encoding="utf-8",
    )

    loaded = RulesLoader.load(config)

    assert loaded.nlp.enabled is False
    assert loaded.nlp.auto_download is False
    assert loaded.nlp.provider_order == ("gliner", "spacy", "natasha", "qwen")
    assert loaded.nlp.providers.gliner.model_name == "urchade/gliner_multi-v2.1"
    assert loaded.nlp.providers.gliner.labels == (
        "person",
        "organization",
        "location",
        "address",
    )
    assert loaded.nlp.providers.gliner.enabled is False
    assert loaded.nlp.providers.spacy.model_name == "ru_core_news_lg"
    assert loaded.nlp.providers.spacy.enabled is False
    assert loaded.nlp.providers.natasha.enabled is False
    assert loaded.nlp.providers.qwen.model_name == "Qwen/Qwen2.5-Coder-7B-Instruct"
    assert loaded.nlp.providers.qwen.labels == (
        "person",
        "organization",
        "location",
        "address",
    )
    assert loaded.nlp.providers.qwen.max_new_tokens == 512
    assert loaded.nlp.providers.qwen.enabled is False


def test_rules_loader_loads_nlp_config(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        """
pipeline:
  deterministic_secret: "secret"

nlp:
  enabled: true
  auto_download: true
  min_confidence: 0.65
  provider_order:
    - gliner
    - spacy
    - natasha
  providers:
    gliner:
      enabled: true
      model_name: "custom/gliner"
      model_path: "gliner/model"
      auto_download: false
      labels:
        - person
        - organization
        - bank_account
      device: cpu
      threshold: 0.7
      batch_size: 8
    spacy:
      enabled: true
      model_name: "ru_core_news_sm"
      model_path: "ru_core_news_md"
      auto_download: true
      batch_size: 16
    natasha:
      enabled: true
    qwen:
      enabled: false
      model_name: "Qwen/custom"
      model_path: null
      auto_download: null
      labels:
        - person
        - organization
      device: cpu
      threshold: 0.5
      max_context_chars: 4000
      max_new_tokens: 256

rules:
  person:
    enabled: true
    mode: hmac
    prefix: PERSON
""",
        encoding="utf-8",
    )

    loaded = RulesLoader.load(config)

    assert loaded.nlp.enabled is True
    assert loaded.nlp.auto_download is True
    assert loaded.nlp.min_confidence == 0.65
    assert loaded.nlp.provider_order == ("gliner", "spacy", "natasha")
    assert loaded.nlp.providers.gliner.model_name == "custom/gliner"
    assert loaded.nlp.providers.gliner.model_path == "gliner/model"
    assert loaded.nlp.providers.gliner.auto_download is False
    assert loaded.nlp.providers.gliner.labels == (
        "person",
        "organization",
        "bank_account",
    )
    assert loaded.nlp.providers.gliner.threshold == 0.7
    assert loaded.nlp.providers.gliner.batch_size == 8
    assert loaded.nlp.providers.spacy.model_name == "ru_core_news_sm"
    assert loaded.nlp.providers.spacy.model_path == "ru_core_news_md"
    assert loaded.nlp.providers.spacy.auto_download is True
    assert loaded.nlp.providers.spacy.batch_size == 16
    assert loaded.nlp.providers.natasha.enabled is True
    assert loaded.nlp.providers.qwen.model_name == "Qwen/custom"
    assert loaded.nlp.providers.qwen.labels == ("person", "organization")
    assert loaded.nlp.providers.qwen.max_new_tokens == 256


def test_rules_loader_applies_nlp_env_overrides(
    tmp_path: Path,
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

    config = tmp_path / "config.yaml"
    config.write_text(
        """
pipeline:
  deterministic_secret: "secret"

rules:
  email:
    enabled: true
    mode: hmac
    prefix: EMAIL
""",
        encoding="utf-8",
    )

    loaded = RulesLoader.load(config)

    assert loaded.nlp.enabled is True
    assert loaded.nlp.auto_download is True
    assert loaded.nlp.providers.gliner.enabled is True
    assert loaded.nlp.providers.gliner.model_name == "env/gliner"
    assert loaded.nlp.providers.gliner.model_path == "gliner/env"
    assert loaded.nlp.providers.gliner.device == "cuda:0"
    assert loaded.nlp.providers.spacy.enabled is True
    assert loaded.nlp.providers.spacy.model_name == "ru_core_news_sm"
    assert loaded.nlp.providers.spacy.model_path == "spacy/env"
    assert loaded.nlp.providers.natasha.enabled is True
    assert loaded.nlp.providers.qwen.enabled is True
    assert loaded.nlp.providers.qwen.model_name == "Qwen/example"
    assert loaded.nlp.providers.qwen.model_path == "qwen/env"
    assert loaded.nlp.providers.qwen.device == "cuda:1"


def test_rules_loader_ignores_empty_nlp_env_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MASKFLOW_NLP_ENABLED", "")
    monkeypatch.setenv("MASKFLOW_GLINER_MODEL", "")
    monkeypatch.setenv("MASKFLOW_GLINER_MODEL_PATH", "")
    monkeypatch.setenv("MASKFLOW_SPACY_MODEL_PATH", "")
    monkeypatch.setenv("MASKFLOW_QWEN_MODEL_PATH", "")

    config = tmp_path / "config.yaml"
    config.write_text(
        """
pipeline:
  deterministic_secret: "secret"

nlp:
  enabled: true
  providers:
    gliner:
      model_name: "yaml/gliner"
      model_path: "yaml/gliner-path"
    spacy:
      model_path: "yaml/spacy-path"
    qwen:
      model_path: "yaml/qwen-path"

rules:
  email:
    enabled: true
    mode: hmac
    prefix: EMAIL
""",
        encoding="utf-8",
    )

    loaded = RulesLoader.load(config)

    assert loaded.nlp.enabled is True
    assert loaded.nlp.providers.gliner.model_name == "yaml/gliner"
    assert loaded.nlp.providers.gliner.model_path == "yaml/gliner-path"
    assert loaded.nlp.providers.spacy.model_path == "yaml/spacy-path"
    assert loaded.nlp.providers.qwen.model_path == "yaml/qwen-path"


def test_nlp_example_config_loads() -> None:
    loaded = RulesLoader.load(Path("configs/examples/nlp.yaml"), validate_secret=False)

    assert loaded.nlp.enabled is True
    assert loaded.nlp.providers.gliner.enabled is True
    assert loaded.rules["person"].enabled is True
    assert loaded.rules["organization"].prefix == "ORG"
