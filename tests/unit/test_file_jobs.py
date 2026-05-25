from pathlib import Path

import pytest

from maskflow.runtime.paths import get_runtime_paths
from maskflow.runtime.settings import get_settings
from maskflow.services.file_jobs import FileMaskingJobService, ensure_supported_extension


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


def test_file_masking_job_service_processes_supported_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MASKFLOW_DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()

    try:
        config = tmp_path / "config.yaml"
        source = tmp_path / "source.txt"
        write_config(config)
        source.write_text("Contact: admin@example.com", encoding="utf-8")

        result = FileMaskingJobService(paths=get_runtime_paths()).process_file(
            source_path=source,
            original_name="source.txt",
            config_path=config,
        )

        masked = result.output_path.read_text(encoding="utf-8")

        assert result.output_path.exists()
        assert result.report_path.exists()
        assert "admin@example.com" not in masked
        assert "EMAIL_" in masked
        assert result.report.matches_applied == 1
    finally:
        get_settings.cache_clear()


def test_file_masking_job_service_rejects_unsupported_extension() -> None:
    with pytest.raises(ValueError, match="Unsupported file format"):
        ensure_supported_extension("source.pdf")
