import time
from collections import Counter
from collections.abc import Iterable

from maskflow.core.interfaces import BaseDetector, BaseMasker
from maskflow.core.types import AnalysisResult, Match
from maskflow.utils.logging import get_logger

logger = get_logger("maskflow.engine")


class MaskingEngine:
    def __init__(
        self,
        detectors: list[BaseDetector],
        maskers: dict[str, BaseMasker],
    ) -> None:
        self.detectors = detectors
        self.maskers = maskers

    def process_text(self, text: str) -> str:
        matches, detector_timings_ms = self._collect_matches(text)
        resolved_matches = self._resolve_overlaps(matches)
        detector_counts = Counter(match.detector for match in resolved_matches)

        logger.debug(
            "text_processed",
            matches_found=len(matches),
            matches_applied=len(resolved_matches),
            matches_skipped=len(matches) - len(resolved_matches),
            detector_counts=dict(detector_counts),
            detector_timings_ms=detector_timings_ms,
        )

        return self._apply_masks(text, resolved_matches)

    def _collect_matches(self, text: str) -> tuple[list[Match], dict[str, int]]:
        matches: list[Match] = []
        detector_timings_ms: dict[str, int] = {}

        for detector in self.detectors:
            started_at = time.perf_counter()
            detector_matches = list(detector.detect(text))

            detector_timings_ms[detector.name] = int(
                (time.perf_counter() - started_at) * 1000,
            )

            matches.extend(detector_matches)

        return matches, detector_timings_ms

    def _resolve_overlaps(self, matches: list[Match]) -> list[Match]:
        sorted_matches = sorted(
            matches,
            key=lambda match: (match.start, -match.length),
        )

        resolved: list[Match] = []
        last_end = -1

        for match in sorted_matches:
            if match.start < last_end:
                continue

            resolved.append(match)
            last_end = match.end

        return resolved

    def _apply_masks(
        self,
        text: str,
        matches: Iterable[Match],
    ) -> str:
        result: list[str] = []
        last_index = 0

        for match in matches:
            masker = self.maskers.get(match.detector)

            if masker is None:
                # FIX 1.3: явный pass-through — включаем текст матча как есть
                # и обновляем last_index, чтобы следующая итерация не дублировала текст.
                logger.warning(
                    "no_masker_for_detector",
                    detector=match.detector,
                    note="match passed through unmasked",
                )
                result.append(text[last_index : match.end])
                last_index = match.end
                continue

            result.append(text[last_index : match.start])
            result.append(masker.mask(match.value))

            last_index = match.end

        result.append(text[last_index:])

        return "".join(result)

    def analyze_text(self, text: str) -> AnalysisResult:
        matches, detector_timings_ms = self._collect_matches(text)
        resolved_matches = self._resolve_overlaps(matches)

        detector_counts = Counter(match.detector for match in resolved_matches)

        return AnalysisResult(
            matches_found=len(matches),
            matches_applied=len(resolved_matches),
            matches_skipped=len(matches) - len(resolved_matches),
            detector_counts=dict(detector_counts),
            detector_timings_ms=detector_timings_ms,
        )

    def process_with_stats(self, text: str) -> tuple[str, AnalysisResult]:
        """Single-pass: маскирует и возвращает статистику за один проход."""
        matches, detector_timings_ms = self._collect_matches(text)
        resolved_matches = self._resolve_overlaps(matches)
        detector_counts = Counter(match.detector for match in resolved_matches)

        masked = self._apply_masks(text, resolved_matches)

        logger.debug(
            "text_processed_with_stats",
            matches_found=len(matches),
            matches_applied=len(resolved_matches),
            matches_skipped=len(matches) - len(resolved_matches),
            detector_counts=dict(detector_counts),
            detector_timings_ms=detector_timings_ms,
        )

        analysis = AnalysisResult(
            matches_found=len(matches),
            matches_applied=len(resolved_matches),
            matches_skipped=len(matches) - len(resolved_matches),
            detector_counts=dict(detector_counts),
            detector_timings_ms=detector_timings_ms,
        )

        return masked, analysis
