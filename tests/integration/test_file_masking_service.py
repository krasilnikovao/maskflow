from pathlib import Path

import pytest

from maskflow.services.file_masking import FileMaskingService


def write_config(path: Path) -> None:
    path.write_text(
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


def test_file_masking_service_rejects_existing_destination(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    source = tmp_path / "source.txt"
    destination = tmp_path / "masked.txt"

    write_config(config)
    source.write_text("Contact: admin@example.com", encoding="utf-8")
    destination.write_text("existing", encoding="utf-8")

    service = FileMaskingService()

    with pytest.raises(FileExistsError, match="Destination already exists"):
        service.process_file(
            source=source,
            destination=destination,
            config_path=config,
        )

    assert destination.read_text(encoding="utf-8") == "existing"


def test_file_masking_service_overwrites_when_enabled(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    source = tmp_path / "source.txt"
    destination = tmp_path / "masked.txt"

    write_config(config)
    source.write_text("Contact: admin@example.com", encoding="utf-8")
    destination.write_text("existing", encoding="utf-8")

    service = FileMaskingService()

    service.process_file(
        source=source,
        destination=destination,
        config_path=config,
        overwrite=True,
    )

    result = destination.read_text(encoding="utf-8")

    assert "existing" not in result
    assert "admin@example.com" not in result
    assert "EMAIL_" in result
