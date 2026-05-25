"""SQL-процессор с контекстной маскировкой.

Стратегия: маскируются только значения внутри одинарных кавычек ('...').
Синтаксические элементы SQL — ключевые слова, идентификаторы, числа вне строк,
операторы — остаются нетронутыми.

Почему не полный AST-парсинг:
  - Потребовал бы знания диалекта (MySQL, PostgreSQL, MSSQL, 1C-SQL, ...)
  - sqlparse не поддерживает все кириллические идентификаторы 1С
  - Для дампов INSERT/UPDATE с PII в строковых литералах этого подхода достаточно

Ограничения:
  - Не маскирует числовые значения вне кавычек (телефоны, ИНН в integer-колонках)
  - Не распознаёт $-quoted строки PostgreSQL ($$...$$)
  - Не учитывает escape-последовательности диалектов (\\' vs '')
    — используется экранирование '' (стандарт SQL)

Streaming: файл обрабатывается построчно, что позволяет работать с
multi-GB дампами без загрузки в память.
"""

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import regex

from maskflow.core.engine import MaskingEngine
from maskflow.core.types import AnalysisResult
from maskflow.utils.atomic import atomic_write_binary_via_temp
from maskflow.utils.encoding import detect_text_encoding

# Паттерн для одинарно-кавычных строк SQL.
# Учитывает экранирование через '' (SQL-standard) и через \' (MySQL/MSSQL).
# Группа 1 (quoted_value) — содержимое без кавычек.
_SQL_STRING_RE = regex.compile(
    r"""
    '                           # открывающая кавычка
    (?P<quoted_value>
        (?:
            ''                  # экранированная кавычка SQL-style ('')
            | \\'               # экранированная кавычка backslash-style (\')
            | [^'\\]            # любой другой символ
        )*
    )
    '                           # закрывающая кавычка
    """,
    regex.VERBOSE,
)


@dataclass(slots=True)
class _SqlStats:
    matches_found: int = 0
    matches_applied: int = 0
    matches_skipped: int = 0
    detector_counts: Counter[str] = field(default_factory=Counter)
    detector_timings_ms: Counter[str] = field(default_factory=Counter)


class SqlProcessor:
    """SQL-процессор: маскирует только содержимое строковых литералов.

    Принцип работы:
      1. Строка разбивается на токены: SQL_STRING | OTHER_TEXT
      2. Маскировочный движок применяется только к SQL_STRING токенам
      3. Структура SQL (ключевые слова, идентификаторы, числа) не затрагивается
    """

    def __init__(self, engine: MaskingEngine) -> None:
        self.engine = engine

    def _resolve_encoding(self, source: Path, encoding: str | None) -> str:
        if encoding is not None:
            return encoding
        return detect_text_encoding(source)

    def _mask_sql_line(
        self,
        line: str,
        stats: _SqlStats | None,
    ) -> str:
        """Маскирует строковые литералы в одной строке SQL."""
        result: list[str] = []
        last_end = 0

        for match in _SQL_STRING_RE.finditer(line):
            # Добавляем SQL-текст до строкового литерала без изменений
            result.append(line[last_end : match.start()])

            raw_value = match.group("quoted_value")

            if stats is not None:
                masked_value, analysis = self.engine.process_with_stats(raw_value)
                stats.matches_found += analysis.matches_found
                stats.matches_applied += analysis.matches_applied
                stats.matches_skipped += analysis.matches_skipped
                stats.detector_counts.update(analysis.detector_counts)
                stats.detector_timings_ms.update(analysis.detector_timings_ms)
            else:
                masked_value = self.engine.process_text(raw_value)

            # Восстанавливаем кавычки вокруг (возможно) замаскированного значения
            result.append(f"'{masked_value}'")
            last_end = match.end()

        # Добавляем остаток строки после последнего строкового литерала
        result.append(line[last_end:])
        return "".join(result)

    def _write_masked_sql(
        self,
        source: Path,
        destination: Path,
        encoding: str,
        stats: _SqlStats | None,
    ) -> None:
        """Построчная запись с маскировкой строковых литералов."""
        with (
            source.open(encoding=encoding, errors="replace", newline="") as src,
            destination.open("w", encoding=encoding, newline="") as dst,
        ):
            for line in src:
                dst.write(self._mask_sql_line(line, stats))

    def process(
        self,
        source: Path,
        destination: Path,
        encoding: str | None = None,
    ) -> None:
        effective_encoding = self._resolve_encoding(source, encoding)
        atomic_write_binary_via_temp(
            destination=destination,
            writer=lambda temp_path: self._write_masked_sql(
                source, temp_path, effective_encoding, stats=None
            ),
        )

    def process_with_stats(
        self,
        source: Path,
        destination: Path,
        encoding: str | None = None,
    ) -> AnalysisResult:
        """Single-pass: маскирует и собирает статистику за один проход."""
        effective_encoding = self._resolve_encoding(source, encoding)
        stats = _SqlStats()

        atomic_write_binary_via_temp(
            destination=destination,
            writer=lambda temp_path: self._write_masked_sql(
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
        """Анализирует без записи: считает потенциальные маски в строковых литералах."""
        effective_encoding = self._resolve_encoding(source, encoding)

        total_matches_found = 0
        total_matches_applied = 0
        total_matches_skipped = 0
        detector_counts: Counter[str] = Counter()
        detector_timings_ms: Counter[str] = Counter()

        with source.open(encoding=effective_encoding, errors="replace", newline="") as src:
            for line in src:
                for match in _SQL_STRING_RE.finditer(line):
                    raw_value = match.group("quoted_value")
                    analysis = self.engine.analyze_text(raw_value)

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
