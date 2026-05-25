import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from maskflow.core.directory import SUPPORTED_EXTENSIONS
from maskflow.reports.json_report import export_batch_report_json
from maskflow.reports.models import AggregateStatistics, BatchProcessingReport, FileProcessingReport
from maskflow.runtime.paths import RuntimePaths, get_runtime_paths
from maskflow.services.demasking import DemaskingService
from maskflow.services.file_masking import FileMaskingService

_SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True, slots=True)
class FileMaskingJobResult:
    job_id: str
    original_name: str
    source_path: Path
    output_path: Path
    report_path: Path
    report: FileProcessingReport


@dataclass(frozen=True, slots=True)
class FileDemaskingJobResult:
    job_id: str
    original_name: str
    source_path: Path
    output_path: Path
    replacements: int
    mapping_size: int


class FileMaskingJobService:
    def __init__(self, paths: RuntimePaths | None = None) -> None:
        self.paths = paths or get_runtime_paths()

    def save_upload(
        self,
        filename: str,
        stream: BinaryIO,
    ) -> Path:
        safe_name = sanitize_filename(filename)
        ensure_supported_extension(safe_name)

        self.paths.ensure_directories()
        upload_dir = self.paths.tmp_dir / uuid.uuid4().hex
        upload_dir.mkdir(parents=True, exist_ok=False)

        source_path = upload_dir / safe_name
        with source_path.open("wb") as destination:
            shutil.copyfileobj(stream, destination)

        return source_path

    def process_file(
        self,
        source_path: Path,
        original_name: str,
        config_path: Path,
        plugins_dir: Path | None = None,
    ) -> FileMaskingJobResult:
        safe_name = sanitize_filename(original_name)
        ensure_supported_extension(safe_name)

        self.paths.ensure_directories()
        job_id = uuid.uuid4().hex
        job_dir = self.paths.jobs_dir / job_id
        input_dir = job_dir / "input"
        output_dir = job_dir / "output"
        input_dir.mkdir(parents=True, exist_ok=False)
        output_dir.mkdir(parents=True, exist_ok=False)

        persisted_source = input_dir / safe_name
        if source_path.resolve() != persisted_source.resolve():
            shutil.copy2(source_path, persisted_source)

        output_path = output_dir / build_masked_filename(safe_name)
        report = FileMaskingService().process_file(
            source=persisted_source,
            destination=output_path,
            config_path=config_path,
            overwrite=False,
            plugins_dir=plugins_dir,
        )

        report_path = self.paths.reports_dir / f"{job_id}.json"
        export_batch_report_json(
            report=BatchProcessingReport(
                total=1,
                success=1 if report.success else 0,
                failed=0 if report.success else 1,
                duration_ms=report.duration_ms,
                files=[report],
                statistics=AggregateStatistics(
                    total_matches_found=report.matches_found,
                    total_matches_applied=report.matches_applied,
                    total_matches_skipped=report.matches_skipped,
                    detector_totals=report.detector_counts,
                    timeout_count=1 if report.timed_out else 0,
                ),
            ),
            destination=report_path,
        )

        return FileMaskingJobResult(
            job_id=job_id,
            original_name=safe_name,
            source_path=persisted_source,
            output_path=output_path,
            report_path=report_path,
            report=report,
        )

    def demask_file(
        self,
        source_path: Path,
        original_name: str,
        config_path: Path,
    ) -> FileDemaskingJobResult:
        safe_name = sanitize_filename(original_name)
        ensure_supported_extension(safe_name)

        self.paths.ensure_directories()
        job_id = uuid.uuid4().hex
        job_dir = self.paths.jobs_dir / job_id
        input_dir = job_dir / "input"
        output_dir = job_dir / "output"
        input_dir.mkdir(parents=True, exist_ok=False)
        output_dir.mkdir(parents=True, exist_ok=False)

        persisted_source = input_dir / safe_name
        if source_path.resolve() != persisted_source.resolve():
            shutil.copy2(source_path, persisted_source)

        output_path = output_dir / build_demasked_filename(safe_name)
        result = DemaskingService().demask_file(
            source=persisted_source,
            destination=output_path,
            config_path=config_path,
        )

        return FileDemaskingJobResult(
            job_id=job_id,
            original_name=safe_name,
            source_path=persisted_source,
            output_path=output_path,
            replacements=result.replacements,
            mapping_size=result.mapping_size,
        )


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name.strip()
    if not name:
        raise ValueError("File name is required")

    safe_name = _SAFE_FILENAME_PATTERN.sub("_", name)
    if safe_name in {".", ".."}:
        raise ValueError("Invalid file name")

    return safe_name


def ensure_supported_extension(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Unsupported file format: {suffix or '(none)'}. Supported: {supported}")


def build_masked_filename(filename: str) -> str:
    path = Path(filename)
    return f"{path.stem}.masked{path.suffix.lower()}"


def build_demasked_filename(filename: str) -> str:
    path = Path(filename)
    return f"{path.stem}.demasked{path.suffix.lower()}"
