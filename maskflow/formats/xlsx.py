from collections import Counter

from openpyxl import load_workbook  # type: ignore[import-untyped]
from openpyxl.worksheet.worksheet import Worksheet  # type: ignore[import-untyped]

from maskflow.core.engine import MaskingEngine
from maskflow.core.types import AnalysisResult


class XlsxProcessor:
    def __init__(self, engine: MaskingEngine) -> None:
        self.engine = engine

    def analyze(self, source: str) -> AnalysisResult:
        workbook = load_workbook(source)

        total_matches_found = 0
        total_matches_applied = 0
        total_matches_skipped = 0
        detector_counts: Counter[str] = Counter()
        detector_timings_ms: Counter[str] = Counter()

        for sheet in workbook.worksheets:
            if not isinstance(sheet, Worksheet):
                continue

            for row in sheet.iter_rows():
                for cell in row:
                    if not isinstance(cell.value, str):
                        continue

                    if cell.value.startswith("="):
                        continue

                    analysis = self.engine.analyze_text(cell.value)

                    total_matches_found += analysis.matches_found
                    total_matches_applied += analysis.matches_applied
                    total_matches_skipped += analysis.matches_skipped
                    detector_counts.update(analysis.detector_counts)
                    detector_timings_ms.update(analysis.detector_timings_ms)

        return AnalysisResult(
            matches_found=total_matches_found,
            matches_applied=total_matches_applied,
            matches_skipped=total_matches_skipped,
            detector_counts=dict(detector_counts),
            detector_timings_ms=dict(detector_timings_ms),
        )

    def process(self, source: str, destination: str) -> None:
        workbook = load_workbook(source)

        for sheet in workbook.worksheets:
            if not isinstance(sheet, Worksheet):
                continue

            for row in sheet.iter_rows():
                for cell in row:
                    if not isinstance(cell.value, str):
                        continue

                    if cell.value.startswith("="):
                        continue

                    cell.value = self.engine.process_text(cell.value)

        workbook.save(destination)
