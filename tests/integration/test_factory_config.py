from pathlib import Path

import pytest

from maskflow.core.factory import build_engine_bundle_from_config
from maskflow.rules.loader import RulesLoader


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


def test_factory_rejects_unsupported_masking_mode(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
pipeline:
  deterministic_secret: "secret"

rules:
  email:
    enabled: true
    mode: unsupported
    prefix: EMAIL
""",
        encoding="utf-8",
    )

    config = RulesLoader.load(config_path)

    with pytest.raises(ValueError, match="Unsupported masking mode: unsupported"):
        build_engine_bundle_from_config(config)
