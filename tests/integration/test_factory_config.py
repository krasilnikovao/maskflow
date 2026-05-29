from collections.abc import Iterable
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from maskflow.core.factory import build_engine_bundle_from_config
from maskflow.nlp.models import EntityCandidate
from maskflow.nlp.pipeline import NlpPipeline
from maskflow.nlp.providers.base import NlpProvider
from maskflow.rules.loader import RulesLoader
from maskflow.rules.models import NlpConfig


def test_factory_builds_engine_from_yaml_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
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

    config = RulesLoader.load(config_path)
    bundle = build_engine_bundle_from_config(config)
    engine = bundle.engine

    result = engine.process_text("Contact: admin@example.com")

    assert "admin@example.com" not in result
    assert "EMAIL_" in result


def test_factory_respects_disabled_rules(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
pipeline:
  deterministic_secret: "secret"

rules:
  email:
    enabled: false
    mode: hmac
    prefix: EMAIL
""",
        encoding="utf-8",
    )

    config = RulesLoader.load(config_path)
    bundle = build_engine_bundle_from_config(config)
    engine = bundle.engine

    result = engine.process_text("Contact: admin@example.com")

    assert result == "Contact: admin@example.com"


def test_factory_rejects_unknown_rule(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
pipeline:
  deterministic_secret: "secret"

rules:
  unknown:
    enabled: true
    mode: hmac
    prefix: UNKNOWN
""",
        encoding="utf-8",
    )

    config = RulesLoader.load(config_path)

    with pytest.raises(ValueError, match="Unknown rule: unknown"):
        build_engine_bundle_from_config(config)


def test_factory_rejects_unimplemented_masking_mode(tmp_path: Path) -> None:
    """Modes that are valid in the config schema but not yet implemented
    must raise NotImplementedError at engine-build time, not at load time.

    'partial' is a recognised MaskingMode literal so Pydantic accepts the
    config; but no masker implementation exists for it yet, so the factory
    should raise NotImplementedError.
    """
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
pipeline:
  deterministic_secret: "secret"

rules:
  email:
    enabled: true
    mode: partial
    prefix: EMAIL
""",
        encoding="utf-8",
    )

    config = RulesLoader.load(config_path)

    with pytest.raises(NotImplementedError, match="partial"):
        build_engine_bundle_from_config(config)


def test_factory_rejects_nlp_rule_without_enabled_nlp(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
pipeline:
  deterministic_secret: "secret"

rules:
  person:
    enabled: true
    mode: hmac
    prefix: PERSON
""",
        encoding="utf-8",
    )

    config = RulesLoader.load(config_path)

    with pytest.raises(ValueError, match="requires nlp.enabled=true"):
        build_engine_bundle_from_config(config)


class FakeNlpProvider(NlpProvider):
    name = "fake"

    def detect(self, text: str) -> Iterable[EntityCandidate]:
        start = text.index("Иван Петров")
        end = start + len("Иван Петров")
        yield EntityCandidate(
            entity_type="person",
            start=start,
            end=end,
            value=text[start:end],
            source=self.name,
            confidence=1.0,
        )


def test_factory_registers_nlp_detector_and_entity_masker(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
pipeline:
  deterministic_secret: "secret"

nlp:
  enabled: true
  min_confidence: 0.5
  provider_order:
    - natasha
  providers:
    gliner:
      enabled: false
      model_path: null
      device: cpu
      threshold: 0.5
      batch_size: 16
    spacy:
      enabled: false
      model_path: null
      batch_size: 32
    natasha:
      enabled: true
    qwen:
      enabled: false
      model_path: null
      device: cpu
      threshold: 0.5
      max_context_chars: 4000

rules:
  person:
    enabled: true
    mode: hmac
    prefix: PERSON
""",
        encoding="utf-8",
    )

    config = RulesLoader.load(config_path)

    def fake_build_nlp_pipeline(_config: NlpConfig) -> NlpPipeline:
        return NlpPipeline(providers=[FakeNlpProvider()])

    monkeypatch.setattr(
        "maskflow.core.factory.build_nlp_pipeline",
        fake_build_nlp_pipeline,
    )

    bundle = build_engine_bundle_from_config(config)

    result = bundle.engine.process_text("Клиент Иван Петров пришел")

    assert "Иван Петров" not in result
    assert "PERSON_" in result


def test_factory_registers_default_nlp_entity_maskers_when_nlp_enabled(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
pipeline:
  deterministic_secret: "secret"

nlp:
  enabled: true
  min_confidence: 0.5
  provider_order:
    - natasha
  providers:
    natasha:
      enabled: true

rules:
  email:
    enabled: true
    mode: hmac
    prefix: EMAIL
""",
        encoding="utf-8",
    )

    config = RulesLoader.load(config_path)

    def fake_build_nlp_pipeline(_config: NlpConfig) -> NlpPipeline:
        return NlpPipeline(providers=[FakeNlpProvider()])

    monkeypatch.setattr(
        "maskflow.core.factory.build_nlp_pipeline",
        fake_build_nlp_pipeline,
    )

    bundle = build_engine_bundle_from_config(config)

    result = bundle.engine.process_text("Клиент Иван Петров пришел")

    assert "Иван Петров" not in result
    assert "PERSON_" in result
