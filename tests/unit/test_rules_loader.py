from pathlib import Path

import pytest

from maskflow.rules.loader import RulesLoader


def test_rules_loader_loads_valid_config(tmp_path: Path) -> None:
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

    assert loaded.pipeline.deterministic_secret == "secret"
    assert loaded.rules["email"].enabled is True
    assert loaded.rules["email"].mode == "hmac"
    assert loaded.rules["email"].prefix == "EMAIL"


def test_rules_loader_rejects_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yaml"

    with pytest.raises(FileNotFoundError):
        RulesLoader.load(missing)


def test_rules_loader_rejects_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Config path is not a file"):
        RulesLoader.load(tmp_path)


def test_rules_loader_rejects_non_object_yaml(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text("- item", encoding="utf-8")

    with pytest.raises(ValueError, match="Config root must be a YAML object"):
        RulesLoader.load(config)


def test_rules_loader_can_skip_secret_validation(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        """
pipeline:
  deterministic_secret: "set-via-MASKFLOW_SECRET"

rules:
  email:
    enabled: true
    mode: hmac
    prefix: EMAIL
""",
        encoding="utf-8",
    )

    loaded = RulesLoader.load(config, validate_secret=False)

    assert loaded.pipeline.deterministic_secret == "set-via-MASKFLOW_SECRET"
