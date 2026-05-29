from pathlib import Path
from typing import Any

from pytest import MonkeyPatch
from typer.testing import CliRunner

from maskflow.cli.app import app

runner = CliRunner()


def test_cli_masks_txt_file(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    source = tmp_path / "source.txt"
    destination = tmp_path / "masked.txt"

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

    source.write_text("Contact: admin@example.com", encoding="utf-8")

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
    assert destination.exists()

    masked = destination.read_text(encoding="utf-8")

    assert "admin@example.com" not in masked
    assert "EMAIL_" in masked


def test_cli_rejects_unsupported_format(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    source = tmp_path / "source.unsupported"
    destination = tmp_path / "masked.unsupported"

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

    source.write_text("Contact: admin@example.com", encoding="utf-8")

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
    assert "Unsupported file format" in result.output

    def test_cli_dry_run_does_not_create_destination_file(tmp_path: Path) -> None:
        config = tmp_path / "config.yaml"
        source = tmp_path / "source.txt"
        destination = tmp_path / "masked.txt"

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

        source.write_text("Contact: admin@example.com", encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "mask",
                str(source),
                str(destination),
                "--config",
                str(config),
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "Dry run completed. Matches found: 1" in result.output
        assert not destination.exists()


def test_cli_rejects_existing_destination_without_overwrite(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    source = tmp_path / "source.txt"
    destination = tmp_path / "masked.txt"

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

    source.write_text("Contact: admin@example.com", encoding="utf-8")
    destination.write_text("existing", encoding="utf-8")

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
    assert destination.read_text(encoding="utf-8") == "existing"


def test_cli_overwrites_existing_destination_when_enabled(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    source = tmp_path / "source.txt"
    destination = tmp_path / "masked.txt"

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

    source.write_text("Contact: admin@example.com", encoding="utf-8")
    destination.write_text("existing", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "mask",
            str(source),
            str(destination),
            "--config",
            str(config),
            "--overwrite",
        ],
    )

    assert result.exit_code == 0

    masked = destination.read_text(encoding="utf-8")

    assert "existing" not in masked
    assert "admin@example.com" not in masked
    assert "EMAIL_" in masked


def test_cli_mask_dir_processes_files_recursively(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    source_dir = tmp_path / "source"
    destination_dir = tmp_path / "destination"

    nested_dir = source_dir / "nested"
    nested_dir.mkdir(parents=True)

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

    (source_dir / "a.txt").write_text(
        "Contact: admin@example.com",
        encoding="utf-8",
    )
    (nested_dir / "b.txt").write_text(
        "Contact: user@example.com",
        encoding="utf-8",
    )
    (nested_dir / "ignored.pdf").write_text(
        "Contact: ignored@example.com",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "mask-dir",
            str(source_dir),
            str(destination_dir),
            "--config",
            str(config),
        ],
    )

    assert result.exit_code == 0
    assert (destination_dir / "a.txt").exists()
    assert (destination_dir / "nested" / "b.txt").exists()
    assert not (destination_dir / "nested" / "ignored.pdf").exists()

    first = (destination_dir / "a.txt").read_text(encoding="utf-8")
    second = (destination_dir / "nested" / "b.txt").read_text(encoding="utf-8")

    assert "admin@example.com" not in first
    assert "user@example.com" not in second
    assert "EMAIL_" in first
    assert "EMAIL_" in second


def test_cli_mask_dir_rejects_existing_destination_without_overwrite(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    source_dir = tmp_path / "source"
    destination_dir = tmp_path / "destination"

    source_dir.mkdir()
    destination_dir.mkdir()

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

    (source_dir / "a.txt").write_text(
        "Contact: admin@example.com",
        encoding="utf-8",
    )
    (destination_dir / "a.txt").write_text(
        "existing",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "mask-dir",
            str(source_dir),
            str(destination_dir),
            "--config",
            str(config),
        ],
    )

    assert result.exit_code != 0
    assert (destination_dir / "a.txt").read_text(encoding="utf-8") == "existing"


def test_cli_mask_dir_overwrites_existing_destination_when_enabled(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    source_dir = tmp_path / "source"
    destination_dir = tmp_path / "destination"

    source_dir.mkdir()
    destination_dir.mkdir()

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

    (source_dir / "a.txt").write_text(
        "Contact: admin@example.com",
        encoding="utf-8",
    )
    (destination_dir / "a.txt").write_text(
        "existing",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "mask-dir",
            str(source_dir),
            str(destination_dir),
            "--config",
            str(config),
            "--overwrite",
        ],
    )

    assert result.exit_code == 0

    masked = (destination_dir / "a.txt").read_text(encoding="utf-8")

    assert "existing" not in masked
    assert "admin@example.com" not in masked
    assert "EMAIL_" in masked


def test_cli_prepare_models_uses_selected_provider(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    config = tmp_path / "config.yaml"
    prepared_path = tmp_path / "models" / "gliner"
    calls: list[dict[str, Any]] = []

    config.write_text(
        """
pipeline:
  deterministic_secret: "set-via-MASKFLOW_SECRET"

nlp:
  enabled: false
  auto_download: false
  providers:
    gliner:
      enabled: false
      model_name: "example/gliner"
      model_path: null
      auto_download: null
      labels:
        - person
      device: cpu
      threshold: 0.5
      batch_size: 16
    spacy:
      enabled: false
      model_name: "ru_core_news_lg"
      model_path: null
      auto_download: null
      batch_size: 32
    natasha:
      enabled: false
    qwen:
      enabled: false
      model_name: "Qwen/example"
      model_path: null
      auto_download: null
      device: cpu
      threshold: 0.5
      max_context_chars: 4000

rules:
  email:
    enabled: true
    mode: hmac
    prefix: EMAIL
""",
        encoding="utf-8",
    )

    def fake_ensure_model_available(**kwargs: Any) -> Path:
        calls.append(kwargs)
        return prepared_path

    monkeypatch.setattr(
        "maskflow.cli.commands.models.ensure_model_available",
        fake_ensure_model_available,
    )

    result = runner.invoke(
        app,
        [
            "prepare-models",
            "--config",
            str(config),
            "--provider",
            "gliner",
            "--auto-download",
        ],
    )

    assert result.exit_code == 0
    assert f"gliner: {prepared_path}" in result.output
    assert calls[0]["model_name"] == "example/gliner"
    assert calls[0]["auto_download"] is True


def test_cli_prepare_models_rejects_unknown_provider(tmp_path: Path) -> None:
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

    result = runner.invoke(
        app,
        [
            "prepare-models",
            "--config",
            str(config),
            "--provider",
            "spacy",
        ],
    )

    assert result.exit_code != 0
    assert "Provider must be one of: gliner, qwen" in result.output
