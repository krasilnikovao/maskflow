from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from maskflow.core.factory import build_engine_bundle_from_config
from maskflow.rules.loader import RulesLoader
from maskflow.runtime.settings import get_settings
from maskflow.services.demasking import DemaskingService


def write_reversible_config(path: Path) -> None:
    path.write_text(
        """
pipeline:
  deterministic_secret: "secret"

rules:
  email:
    enabled: true
    mode: hmac
    prefix: EMAIL

reversible_mapping:
  enabled: true
  path: "reversible/reversible-map.bin"
  encryption_key_env: "MASKFLOW_TEST_REVERSIBLE_KEY"
""",
        encoding="utf-8",
    )


def test_demasking_service_restores_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MASKFLOW_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("MASKFLOW_TEST_REVERSIBLE_KEY", Fernet.generate_key().decode("utf-8"))
    get_settings.cache_clear()

    try:
        config_path = tmp_path / "config.yaml"
        write_reversible_config(config_path)

        config = RulesLoader.load(config_path)
        bundle = build_engine_bundle_from_config(config)
        masked = bundle.engine.process_text("Contact: admin@example.com")
        bundle.save()

        demasked, result = DemaskingService().demask_text(
            text=masked,
            config_path=config_path,
        )

        assert demasked == "Contact: admin@example.com"
        assert result.replacements == 1
        assert result.mapping_size == 1
    finally:
        get_settings.cache_clear()


def test_demasking_service_restores_text_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MASKFLOW_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("MASKFLOW_TEST_REVERSIBLE_KEY", Fernet.generate_key().decode("utf-8"))
    get_settings.cache_clear()

    try:
        config_path = tmp_path / "config.yaml"
        source = tmp_path / "masked.txt"
        destination = tmp_path / "demasked.txt"
        write_reversible_config(config_path)

        config = RulesLoader.load(config_path)
        bundle = build_engine_bundle_from_config(config)
        masked = bundle.engine.process_text("Contact: admin@example.com")
        bundle.save()
        source.write_text(masked, encoding="utf-8")

        result = DemaskingService().demask_file(
            source=source,
            destination=destination,
            config_path=config_path,
        )

        assert destination.read_text(encoding="utf-8") == "Contact: admin@example.com"
        assert result.replacements == 1
    finally:
        get_settings.cache_clear()


def test_demasking_service_requires_enabled_reversible_mapping(tmp_path: Path) -> None:
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

    with pytest.raises(ValueError, match="reversible_mapping is disabled"):
        DemaskingService().demask_text(
            text="EMAIL_123",
            config_path=config_path,
        )
