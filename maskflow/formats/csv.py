import csv
from pathlib import Path

from maskflow.core.engine import MaskingEngine
from maskflow.core.types import AnalysisResult
from maskflow.rules.field_engine import FieldRuleEngine
from maskflow.utils.atomic import atomic_write_binary_via_temp
from maskflow.utils.encoding import detect_text_encoding


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
            ),
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

            for row in reader:
                for cell in row:
                    analysis = self.engine.analyze_text(cell)

                    total_matches_found += analysis.matches_found
                    total_matches_applied += analysis.matches_applied
                    total_matches_skipped += analysis.matches_skipped

                    for detector, count in analysis.detector_counts.items():
                        detector_counts[detector] = detector_counts.get(detector, 0) + count

                    for detector, duration in analysis.detector_timings_ms.items():
                        detector_timings_ms[detector] = (
                            detector_timings_ms.get(detector, 0) + duration
                        )

        return AnalysisResult(
            matches_found=total_matches_found,
            matches_applied=total_matches_applied,
            matches_skipped=total_matches_skipped,
            detector_counts=detector_counts,
            detector_timings_ms=detector_timings_ms,
        )

    def _mask_cell(self, field_name: str, cell: str) -> str:
        if self.field_engine is not None:
            processed = self.field_engine.process_field(
                field_name=field_name,
                value=cell,
            )
            return processed if processed is not None else ""
        return self.engine.process_text(cell)

    def _write_masked_csv(
        self,
        source: Path,
        destination: Path,
        encoding: str,
        delimiter: str,
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
                    writer.writerow([self.engine.process_text(cell) for cell in header])
                else:
                    writer.writerow(header)

                for row in reader:
                    masked_row: list[str] = []

                    for index, cell in enumerate(row):
                        field_name = header[index] if index < len(header) else ""
                        masked_row.append(self._mask_cell(field_name, cell))

                    writer.writerow(masked_row)
