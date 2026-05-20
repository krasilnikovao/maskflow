from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from maskflow.core.engine import MaskingEngine
from maskflow.core.streaming import DEFAULT_CHUNK_SIZE, stream_text_file
from maskflow.core.types import AnalysisResult
from maskflow.utils.atomic import atomic_write_binary_via_temp
from maskflow.utils.encoding import detect_text_encoding

DEFAULT_STREAM_OVERLAP_SIZE = 512


@dataclass(slots=True)
class _StreamStats:
    matches_found: int = 0
    matches_applied: int = 0
    matches_skipped: int = 0
    detector_counts: Counter[str] = field(default_factory=Counter)
    detector_timings_ms: Counter[str] = field(default_factory=Counter)


class TextProcessor:
    def __init__(
        self,
        engine: MaskingEngine,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap_size: int = DEFAULT_STREAM_OVERLAP_SIZE,
    ) -> None:
        if overlap_size < 0:
            raise ValueError("overlap_size must not be negative")

        if overlap_size >= chunk_size:
            raise ValueError("overlap_size must be smaller than chunk_size")

        self.engine = engine
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size

    def _resolve_encoding(self, source: Path, encoding: str | None) -> str:
        if encoding is not None:
            return encoding
        return detect_text_encoding(source)

    def analyze(
        self,
        source: Path,
        encoding: str | None = None,
    ) -> AnalysisResult:
        effective_encoding = self._resolve_encoding(source, encoding)

        total_matches_found = 0
        total_matches_applied = 0
        total_matches_skipped = 0
        detector_counts: Counter[str] = Counter()
        detector_timings_ms: Counter[str] = Counter()

        buffer = ""

        for chunk in stream_text_file(
            source,
            chunk_size=self.chunk_size,
            encoding=effective_encoding,
        ):
            current = buffer + chunk

            if len(current) <= self.overlap_size:
                buffer = current
                continue

            safe_part = current[: -self.overlap_size]
            buffer = current[-self.overlap_size :]

            analysis = self.engine.analyze_text(safe_part)

            total_matches_found += analysis.matches_found
            total_matches_applied += analysis.matches_applied
            total_matches_skipped += analysis.matches_skipped
            detector_counts.update(analysis.detector_counts)
            detector_timings_ms.update(analysis.detector_timings_ms)

        if buffer:
            analysis = self.engine.analyze_text(buffer)

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

    def process(
        self,
        source: Path,
        destination: Path,
        encoding: str | None = None,
    ) -> None:
        effective_encoding = self._resolve_encoding(source, encoding)
        atomic_write_binary_via_temp(
            destination=destination,
            writer=lambda temp_path: self._write_masked_stream(
                source=source,
                destination=temp_path,
                encoding=effective_encoding,
            ),
        )

    def process_with_stats(
        self,
        source: Path,
        destination: Path,
        encoding: str | None = None,
    ) -> AnalysisResult:
        """Single-pass: маскирует и собирает статистику за один проход по файлу."""
        effective_encoding = self._resolve_encoding(source, encoding)
        stats = _StreamStats()

        def writer(temp_path: Path) -> None:
            self._write_masked_stream(
                source=source,
                destination=temp_path,
                encoding=effective_encoding,
                stats=stats,
            )

        atomic_write_binary_via_temp(destination=destination, writer=writer)

        return AnalysisResult(
            matches_found=stats.matches_found,
            matches_applied=stats.matches_applied,
            matches_skipped=stats.matches_skipped,
            detector_counts=dict(stats.detector_counts),
            detector_timings_ms=dict(stats.detector_timings_ms),
        )

    def _write_masked_stream(
        self,
        source: Path,
        destination: Path,
        encoding: str,
        stats: _StreamStats | None = None,
    ) -> None:
        buffer = ""

        with destination.open(
            "w",
            encoding=encoding,
            newline="",
        ) as output:
            for chunk in stream_text_file(
                source,
                chunk_size=self.chunk_size,
                encoding=encoding,
            ):
                current = buffer + chunk

                if len(current) <= self.overlap_size:
                    buffer = current
                    continue

                safe_part = current[: -self.overlap_size]
                buffer = current[-self.overlap_size :]

                output.write(self._process_chunk(safe_part, stats))

            if buffer:
                output.write(self._process_chunk(buffer, stats))

    def _process_chunk(self, chunk: str, stats: _StreamStats | None) -> str:
        if stats is None:
            return self.engine.process_text(chunk)

        masked, analysis = self.engine.process_with_stats(chunk)
        stats.matches_found += analysis.matches_found
        stats.matches_applied += analysis.matches_applied
        stats.matches_skipped += analysis.matches_skipped
        stats.detector_counts.update(analysis.detector_counts)
        stats.detector_timings_ms.update(analysis.detector_timings_ms)
        return masked
