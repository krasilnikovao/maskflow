from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from typer.testing import CliRunner

from maskflow.cli.app import app
from maskflow.storage.encrypted_mapping import EncryptedMappingStore

runner = CliRunner()


def write_config(
    path: Path,
    mapping_path: Path,
) -> None:
    path.write_text(
        f"""
pipeline:
  deterministic_secret: "secret"

rules:
  email:
    enabled: true
    mode: hmac
    prefix: EMAIL

reversible_mapping:
  enabled: true
  path: "{mapping_path.as_posix()}"
  encryption_key_env: "MASKFLOW_TEST_REVERSIBLE_KEY"
""",
        encoding="utf-8",
    )


def test_reversible_mapping_registers_masked_to_original(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    key = Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("MASKFLOW_TEST_REVERSIBLE_KEY", key)

    mapping_path = tmp_path / "reversible-map.bin"
    config = tmp_path / "config.yaml"
    source = tmp_path / "source.txt"
    destination = tmp_path / "masked.txt"

    write_config(config, mapping_path)

    source.write_text(
        "admin@example.com",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "mask",
            str(source),
            str(destination),
            "--config",
            str(config),
        ],
    )

    assert result.exit_code == 0
    assert mapping_path.exists()

    masked = destination.read_text(encoding="utf-8").strip()

    store = EncryptedMappingStore(
        path=mapping_path,
        encryption_key_env="MASKFLOW_TEST_REVERSIBLE_KEY",
    )

    assert store.get(masked) == "admin@example.com"


def test_reversible_mapping_file_does_not_contain_plaintext(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    key = Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("MASKFLOW_TEST_REVERSIBLE_KEY", key)

    mapping_path = tmp_path / "reversible-map.bin"
    config = tmp_path / "config.yaml"
    source = tmp_path / "source.txt"
    destination = tmp_path / "masked.txt"

    write_config(config, mapping_path)

    source.write_text(
        "admin@example.com",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "mask",
            str(source),
            str(destination),
            "--config",
            str(config),
        ],
    )

    assert result.exit_code == 0

    raw_content = mapping_path.read_bytes()

    assert b"admin@example.com" not in raw_content
    assert b"EMAIL_" not in raw_content


def test_reversible_mapping_requires_env_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "MASKFLOW_TEST_REVERSIBLE_KEY",
        raising=False,
    )

    mapping_path = tmp_path / "reversible-map.bin"
    config = tmp_path / "config.yaml"
    source = tmp_path / "source.txt"
    destination = tmp_path / "masked.txt"

    write_config(config, mapping_path)

    source.write_text(
        "admin@example.com",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "mask",
            str(source),
            str(destination),
            "--config",
            str(config),
        ],
    )

    assert result.exit_code != 0
