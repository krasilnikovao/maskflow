import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from maskflow.audit.models import AuditEvent, AuditTrail
from maskflow.core.engine import MaskingEngine
from maskflow.core.factory import build_engine_bundle_from_config
from maskflow.core.types import AnalysisResult
from maskflow.formats.csv import CsvProcessor
from maskflow.formats.docx import DocxProcessor
from maskflow.formats.json import JsonProcessor
from maskflow.formats.sql import SqlProcessor
from maskflow.formats.text import TextProcessor
from maskflow.formats.xlsx import XlsxProcessor
from maskflow.formats.xml import XmlProcessor
from maskflow.reports.models import FileProcessingReport
from maskflow.rules.field_engine import FieldRuleEngine
from maskflow.rules.loader import RulesLoader
from maskflow.utils.atomic import atomic_write_binary_via_temp


@dataclass(frozen=True, slots=True)
class _FormatHandler:
    """Описание обработчика конкретного формата."""

    needs_atomic: bool
    run: Callable[[Path, Path], AnalysisResult]


class FileMaskingService:
    def process_file(
        self,
        source: Path,
        destination: Path,
        config_path: Path,
        overwrite: bool = False,
        plugins_dir: Path | None = None,
    ) -> FileProcessingReport:
        started_at = time.perf_counter()

        audit_trail = AuditTrail()
        audit_trail.add(
            AuditEvent(
                event_type="file_processing_started",
                source=source,
                destination=destination,
                metadata={
                    "suffix": source.suffix.lower(),
                    "overwrite": overwrite,
                },
            ),
        )

        config = RulesLoader.load(config_path)
        bundle = build_engine_bundle_from_config(
            config,
            plugins_dir=plugins_dir,
        )
        engine = bundle.engine

        field_engine = FieldRuleEngine(
            rules=config.field_rules,
            masking_engine=engine,
        )

        suffix = source.suffix.lower()

        if destination.exists() and not overwrite:
            raise FileExistsError(f"Destination already exists: {destination}")

        destination.parent.mkdir(parents=True, exist_ok=True)

        handler = self._build_handler(suffix, engine, field_engine)
        if handler is None:
            raise ValueError(f"Unsupported file format: {suffix}")

        analysis = handler.run(source, destination)

        audit_trail.add(
            AuditEvent(
                event_type="file_processing_finished",
                source=source,
                destination=destination,
                matches_found=analysis.matches_found,
                matches_applied=analysis.matches_applied,
                matches_skipped=analysis.matches_skipped,
                duration_ms=int((time.perf_counter() - started_at) * 1000),
                metadata={"suffix": suffix},
            ),
        )

        bundle.save()

        return FileProcessingReport(
            source=source,
            destination=destination,
            success=True,
            message="OK",
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            matches_found=analysis.matches_found,
            matches_applied=analysis.matches_applied,
            matches_skipped=analysis.matches_skipped,
            detector_counts=analysis.detector_counts,
            detector_timings_ms=analysis.detector_timings_ms,
            audit_trail=audit_trail,
        )

    def _build_handler(
        self,
        suffix: str,
        engine: MaskingEngine,
        field_engine: FieldRuleEngine,
    ) -> _FormatHandler | None:
        if suffix == ".txt":
            text_processor = TextProcessor(engine)

            def run_text(source: Path, destination: Path) -> AnalysisResult:
                # Single-pass: маскируем и собираем счётчики за один проход.
                return text_processor.process_with_stats(source, destination)

            return _FormatHandler(needs_atomic=False, run=run_text)

        if suffix == ".sql":
            sql_processor = SqlProcessor(engine)

            def run_sql(source: Path, destination: Path) -> AnalysisResult:
                return sql_processor.process_with_stats(source, destination)

            return _FormatHandler(needs_atomic=False, run=run_sql)

        if suffix == ".csv":
            csv_processor = CsvProcessor(engine=engine, field_engine=field_engine)

            def run_csv(source: Path, destination: Path) -> AnalysisResult:
                # Single-pass: process_with_stats маскирует и собирает статистику
                # за один проход вместо двух отдельных analyze() + process().
                return csv_processor.process_with_stats(source, destination)

            return _FormatHandler(needs_atomic=False, run=run_csv)

        if suffix == ".xml":
            xml_processor = XmlProcessor(engine=engine, field_engine=field_engine)

            def run_xml(source: Path, destination: Path) -> AnalysisResult:
                # Single-pass: process_with_stats вместо analyze() + process().
                return xml_processor.process_with_stats(source, destination)

            return _FormatHandler(needs_atomic=False, run=run_xml)

        if suffix == ".json":
            json_processor = JsonProcessor(engine=engine, field_engine=field_engine)

            def run_json(source: Path, destination: Path) -> AnalysisResult:
                # Single-pass: process_with_stats вместо analyze() + process().
                return json_processor.process_with_stats(source, destination)

            return _FormatHandler(needs_atomic=False, run=run_json)

        if suffix == ".docx":
            docx_processor = DocxProcessor(engine)

            def run_docx(source: Path, destination: Path) -> AnalysisResult:
                analysis = docx_processor.analyze(source)
                atomic_write_binary_via_temp(
                    destination=destination,
                    writer=lambda temp_path: docx_processor.process(source, temp_path),
                )
                return analysis

            return _FormatHandler(needs_atomic=True, run=run_docx)

        if suffix == ".xlsx":
            xlsx_processor = XlsxProcessor(engine)

            def run_xlsx(source: Path, destination: Path) -> AnalysisResult:
                analysis = xlsx_processor.analyze(source)
                atomic_write_binary_via_temp(
                    destination=destination,
                    writer=lambda temp_path: xlsx_processor.process(source, temp_path),
                )
                return analysis

            return _FormatHandler(needs_atomic=True, run=run_xlsx)

        return None
