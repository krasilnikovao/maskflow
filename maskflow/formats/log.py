"""LOG-процессор: построчная маскировка с защитой структурных элементов.

Стратегия:
  1. Stack traces — строка не маскируется целиком (class names, file paths, line
     numbers не содержат PII и должны оставаться читаемыми для диагностики).
  2. Строки с распознанным префиксом (timestamp + level + logger) — маскируется
     только MESSAGE-часть, структурные поля сохраняются.
  3. Прочие строки — маскируются целиком (safe default).

Поддерживаемые форматы префиксов:
  - ISO 8601 / Python / Java / structlog:
      2024-01-15 10:23:45,123 INFO  root - message
      2024-01-15T10:23:45.123Z [ERROR] message
  - Apache / nginx:
      [15/Jan/2024:10:23:45 +0000] "GET /path HTTP/1.1" 200 ...
  - 1С технологический журнал:
      {10:23:45.123-0,PROC,5}event=Connect,...

Streaming: файл читается построчно, без загрузки в память.
"""

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import regex

from maskflow.core.engine import MaskingEngine
from maskflow.core.types import AnalysisResult
from maskflow.utils.atomic import atomic_write_binary_via_temp
from maskflow.utils.encoding import detect_text_encoding

# ---------------------------------------------------------------------------
# Regex: префикс структурной строки лога
# ---------------------------------------------------------------------------
# Требует наличия timestamp в начале строки — без него строка обрабатывается
# как обычный текст. Это предотвращает ложные срабатывания на вольном тексте.
_LOG_PREFIX_RE = regex.compile(
    r"""
    ^
    (
        # ── ISO 8601 / Python / Java / structlog ────────────────────────────
        # 2024-01-15 10:23:45,123 или 2024-01-15T10:23:45.123Z
        \d{4}-\d{2}-\d{2}[T\x20]\d{2}:\d{2}:\d{2}
        (?:[.,]\d+)?                         # дробные секунды (опционально)
        (?:Z|[+-]\d{2}:?\d{2})?              # timezone (опционально)
        \s*

        |

        # ── Apache / nginx ──────────────────────────────────────────────────
        # [15/Jan/2024:10:23:45 +0000]
        \[\d{1,2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}\s[+-]\d{4}\]
        \s*

        |

        # ── 1С технологический журнал ───────────────────────────────────────
        # {10:23:45.123-0,PROC,5}
        \{\d{2}:\d{2}:\d{2}\.\d+-\d+,\w+,\d+\}
    )

    # Уровень логирования (опционально): [INFO] / INFO / WARN и т.д.
    (?:
        \[?
        (?:TRACE|DEBUG|INFO|INFORMATION|WARNING|WARN|ERROR|CRITICAL|FATAL|SEVERE)
        \]?
        \s*
    )?

    # Имя логгера или компонента (опционально): "root -" / "App:" / "thread-1"
    (?:[\w.$\[\]/-]+\s*[-:|]\s*)?
    """,
    regex.VERBOSE | regex.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Regex: строки stack trace — не маскировать
# ---------------------------------------------------------------------------
_STACK_TRACE_RE = regex.compile(
    r"""
    ^
    (?:
        \s+at\s                  # Java:   "    at com.example.Method(File.java:42)"
        | \s{2,}File\s+"         # Python: '  File "/path/to/file.py", line 42'
        | Caused\x20by:          # Java:   "Caused by: java.lang.NullPointerException"
        | \.\.\.\s+\d+\s+more    # Java:   "... 5 more"
        | \s+\.\.\.\s            # краткие трассировки
    )
    """,
    regex.VERBOSE,
)


@dataclass(slots=True)
class _LogStats:
    matches_found: int = 0
    matches_applied: int = 0
    matches_skipped: int = 0
    detector_counts: Counter[str] = field(default_factory=Counter)
    detector_timings_ms: Counter[str] = field(default_factory=Counter)


class LogProcessor:
    """Построчный LOG-процессор с защитой структурных элементов."""

    def __init__(self, engine: MaskingEngine) -> None:
        self.engine = engine

    def _resolve_encoding(self, source: Path, encoding: str | None) -> str:
        if encoding is not None:
            return encoding
        return detect_text_encoding(source)

    def _mask_log_line(self, line: str, stats: _LogStats | None) -> str:
        """Маскирует одну строку лога с учётом её структуры."""
        # Stack traces — сохраняем нетронутыми
        if _STACK_TRACE_RE.match(line):
            return line

        # Строка с распознанным структурным префиксом:
        # маскируем только message-часть
        prefix_match = _LOG_PREFIX_RE.match(line)
        if prefix_match and prefix_match.end() < len(line):
            prefix = line[: prefix_match.end()]
            message = line[prefix_match.end():]
            return prefix + self._mask_text(message, stats)

        # Fallback: маскируем всю строку
        return self._mask_text(line, stats)

    def _mask_text(self, text: str, stats: _LogStats | None) -> str:
        if stats is None:
            return self.engine.process_text(text)

        masked, analysis = self.engine.process_with_stats(text)
        stats.matches_found += analysis.matches_found
        stats.matches_applied += analysis.matches_applied
        stats.matches_skipped += analysis.matches_skipped
        stats.detector_counts.update(analysis.detector_counts)
        stats.detector_timings_ms.update(analysis.detector_timings_ms)
        return masked

    def _write_masked_log(
        self,
        source: Path,
        destination: Path,
        encoding: str,
        stats: _LogStats | None,
    ) -> None:
        with (
            source.open(encoding=encoding, errors="replace", newline="") as src,
            destination.open("w", encoding=encoding, newline="") as dst,
        ):
            for line in src:
                dst.write(self._mask_log_line(line, stats))

    def process(
        self,
        source: Path,
        destination: Path,
        encoding: str | None = None,
    ) -> None:
        effective_encoding = self._resolve_encoding(source, encoding)
        atomic_write_binary_via_temp(
            destination=destination,
            writer=lambda temp_path: self._write_masked_log(
                source, temp_path, effective_encoding, stats=None
            ),
        )

    def process_with_stats(
        self,
        source: Path,
        destination: Path,
        encoding: str | None = None,
    ) -> AnalysisResult:
        effective_encoding = self._resolve_encoding(source, encoding)
        stats = _LogStats()

        atomic_write_binary_via_temp(
            destination=destination,
            writer=lambda temp_path: self._write_masked_log(
                source, temp_path, effective_encoding, stats=stats
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
    ) -> AnalysisResult:
        """Анализирует без записи: считает потенциальные маски в message-частях."""
        effective_encoding = self._resolve_encoding(source, encoding)

        total_found = 0
        total_applied = 0
        total_skipped = 0
        detector_counts: Counter[str] = Counter()
        detector_timings_ms: Counter[str] = Counter()

        with source.open(encoding=effective_encoding, errors="replace", newline="") as src:
            for line in src:
                if _STACK_TRACE_RE.match(line):
                    continue

                prefix_match = _LOG_PREFIX_RE.match(line)
                text_to_analyze = (
                    line[prefix_match.end():]
                    if prefix_match and prefix_match.end() < len(line)
                    else line
                )

                analysis = self.engine.analyze_text(text_to_analyze)
                total_found += analysis.matches_found
                total_applied += analysis.matches_applied
                total_skipped += analysis.matches_skipped
                detector_counts.update(analysis.detector_counts)
                detector_timings_ms.update(analysis.detector_timings_ms)

        return AnalysisResult(
            matches_found=total_found,
            matches_applied=total_applied,
            matches_skipped=total_skipped,
            detector_counts=dict(detector_counts),
            detector_timings_ms=dict(detector_timings_ms),
        )
