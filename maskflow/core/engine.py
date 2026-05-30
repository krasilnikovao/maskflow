import time
from collections import Counter
from collections.abc import Iterable

from maskflow.core.interfaces import BaseDetector, BaseMasker
from maskflow.core.types import AnalysisResult, Match
from maskflow.utils.logging import get_logger

logger = get_logger("maskflow.engine")

_DETECTOR_PRIORITIES: dict[str, int] = {
    "bank_account": 100,
    "inn": 95,
    "bik": 94,
    "kpp": 90,
    "ogrn": 88,
    "snils": 86,
    "email": 85,
    "phone": 80,
    "guid": 80,
    "ip_address": 75,
    "url": 75,
}
_DEFAULT_DETECTOR_PRIORITY = 10


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
            detector_matches = [
                match
                for match in detector.detect(text)
                if not _is_key_position_match(text, match)
            ]

            detector_timings_ms[detector.name] = int(
                (time.perf_counter() - started_at) * 1000,
            )

            matches.extend(detector_matches)

        return matches, detector_timings_ms

    def _resolve_overlaps(self, matches: list[Match]) -> list[Match]:
        sorted_matches = sorted(
            matches,
            key=lambda match: (
                -_detector_priority(match.detector),
                -match.length,
                match.start,
            ),
        )

        resolved: list[Match] = []

        for match in sorted_matches:
            if any(_overlaps(match, accepted) for accepted in resolved):
                continue

            resolved.append(match)

        return sorted(resolved, key=lambda match: match.start)

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


def _detector_priority(detector: str) -> int:
    return _DETECTOR_PRIORITIES.get(detector, _DEFAULT_DETECTOR_PRIORITY)


def _overlaps(left: Match, right: Match) -> bool:
    return left.start < right.end and right.start < left.end


def _is_key_position_match(text: str, match: Match) -> bool:
    """Return True if the match is a key in a key=value pattern.

    Filters detected spans that are field names rather than values,
    applicable to any key=value format: .env files, config files, logs,
    structured exports, etc.

    Only suppresses a match when it is immediately followed by '='
    (with optional leading spaces). This avoids false negatives caused
    by an unrelated '=' appearing elsewhere on the same line.
    """
    after_match = text[match.end : match.end + 4]
    return after_match.lstrip(" ").startswith("=")
