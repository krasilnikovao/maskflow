import csv
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from maskflow.core.engine import MaskingEngine
from maskflow.core.types import AnalysisResult
from maskflow.rules.field_engine import FieldRuleEngine
from maskflow.utils.atomic import atomic_write_binary_via_temp
from maskflow.utils.encoding import detect_text_encoding


@dataclass(slots=True)
class _CsvStats:
    matches_found: int = 0
    matches_applied: int = 0
    matches_skipped: int = 0
    detector_counts: Counter[str] = field(default_factory=Counter)
    detector_timings_ms: Counter[str] = field(default_factory=Counter)


class CsvProcessor:
    def __init__(
        self,
        engine: MaskingEngine,
        field_engine: FieldRuleEngine | None = None,
        mask_header: bool = False,
    ) -> None:
        self.engine = engine
        self.field_engine = field_engine
        self.mask_header = mask_header

    def _resolve_encoding(self, source: Path, encoding: str | None) -> str:
        return encoding if encoding is not None else detect_text_encoding(source)

    def process(
        self,
        source: Path,
        destination: Path,
        encoding: str | None = None,
        delimiter: str = ",",
    ) -> None:
        effective_encoding = self._resolve_encoding(source, encoding)
        atomic_write_binary_via_temp(
            destination=destination,
            writer=lambda temp_path: self._write_masked_csv(
                source=source,
                destination=temp_path,
                encoding=effective_encoding,
                delimiter=delimiter,
                stats=None,
            ),
        )

    def process_with_stats(
        self,
        source: Path,
        destination: Path,
        encoding: str | None = None,
        delimiter: str = ",",
    ) -> AnalysisResult:
        """FIX 1.2: единый проход — маскируем и собираем статистику."""
        effective_encoding = self._resolve_encoding(source, encoding)
        stats = _CsvStats()

        atomic_write_binary_via_temp(
            destination=destination,
            writer=lambda temp_path: self._write_masked_csv(
                source=source,
                destination=temp_path,
                encoding=effective_encoding,
                delimiter=delimiter,
                stats=stats,
            ),
        )

        return AnalysisResult(
            matches_found=stats.matches_found,
            matches_applied=stats.matches_applied,
            matches_skipped=stats.matches_skipped,
            detector_counts=dict(stats.detector_counts),
            detector_timings_ms=dict(stats.detector_timings_ms),
        )

    def analyze(
        self,
        source: Path,
        encoding: str | None = None,
        delimiter: str = ",",
    ) -> AnalysisResult:
        effective_encoding = self._resolve_encoding(source, encoding)

        total_matches_found = 0
        total_matches_applied = 0
        total_matches_skipped = 0
        detector_counts: dict[str, int] = {}
        detector_timings_ms: dict[str, int] = {}

        with source.open(
            encoding=effective_encoding,
            newline="",
        ) as input_file:
            reader = csv.reader(
                input_file,
                delimiter=delimiter,
            )

            header: list[str] | None = None

            for row_index, row in enumerate(reader):
                # FIX: учитываем mask_header при анализе заголовка
                if row_index == 0:
                    header = row
                    if self.mask_header:
                        for cell in row:
                            analysis = self.engine.analyze_text(cell)
                            total_matches_found += analysis.matches_found
                            total_matches_applied += analysis.matches_applied
                            total_matches_skipped += analysis.matches_skipped
                            for d, c in analysis.detector_counts.items():
                                detector_counts[d] = detector_counts.get(d, 0) + c
                            for d, t in analysis.detector_timings_ms.items():
                                detector_timings_ms[d] = detector_timings_ms.get(d, 0) + t
                    continue

                for index, cell in enumerate(row):
                    field_name = header[index] if header and index < len(header) else ""

                    # Пропускаем поля с remove/replace — реальных матчей не будет
                    if self.field_engine is not None and field_name:
                        rule = self.field_engine.rules.get(field_name.lower())
                        if rule is not None and rule.action in {"remove", "replace"}:
                            continue

                    analysis = self.engine.analyze_text(cell)

                    total_matches_found += analysis.matches_found
                    total_matches_applied += analysis.matches_applied
                    total_matches_skipped += analysis.matches_skipped

                    for d, c in analysis.detector_counts.items():
                        detector_counts[d] = detector_counts.get(d, 0) + c

                    for d, t in analysis.detector_timings_ms.items():
                        detector_timings_ms[d] = detector_timings_ms.get(d, 0) + t

        return AnalysisResult(
            matches_found=total_matches_found,
            matches_applied=total_matches_applied,
            matches_skipped=total_matches_skipped,
            detector_counts=detector_counts,
            detector_timings_ms=detector_timings_ms,
        )

    def _mask_cell(
        self,
        field_name: str,
        cell: str,
        stats: _CsvStats | None,
    ) -> str:
        if self.field_engine is not None:
            rule = self.field_engine.rules.get(field_name.lower()) if field_name else None
            if rule is not None and rule.action in {"remove", "replace"}:
                # Нет маскирования — статистику не собираем
                processed = self.field_engine.process_field(field_name, cell)
                return processed if processed is not None else ""

        if stats is not None:
            masked, analysis = self.engine.process_with_stats(cell)
            stats.matches_found += analysis.matches_found
            stats.matches_applied += analysis.matches_applied
            stats.matches_skipped += analysis.matches_skipped
            stats.detector_counts.update(analysis.detector_counts)
            stats.detector_timings_ms.update(analysis.detector_timings_ms)
            return masked

        return self.engine.process_text(cell)

    def _write_masked_csv(
        self,
        source: Path,
        destination: Path,
        encoding: str,
        delimiter: str,
        stats: _CsvStats | None,
    ) -> None:
        with source.open(
            encoding=encoding,
            newline="",
        ) as input_file:
            with destination.open(
                "w",
                encoding=encoding,
                newline="",
            ) as output_file:
                reader = csv.reader(
                    input_file,
                    delimiter=delimiter,
                )

                writer = csv.writer(
                    output_file,
                    delimiter=delimiter,
                )

                header = next(reader, None)

                if header is None:
                    return

                if self.mask_header:
                    masked_header = [self._mask_cell("", cell, stats) for cell in header]
                    writer.writerow(masked_header)
                else:
                    writer.writerow(header)

                for row in reader:
                    masked_row: list[str] = []

                    for index, cell in enumerate(row):
                        field_name = header[index] if index < len(header) else ""
                        masked_row.append(self._mask_cell(field_name, cell, stats))

                    writer.writerow(masked_row)
