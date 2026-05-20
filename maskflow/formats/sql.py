from pathlib import Path

from maskflow.core.engine import MaskingEngine
from maskflow.core.types import AnalysisResult
from maskflow.formats.text import TextProcessor


class SqlProcessor:
    """SQL обрабатывается как plain text.

    Полноценный парсинг SQL (через sqlparse) пока не реализован —
    он потребовал бы знания схемы таблиц и контекста колонок. Текущая
    реализация полагается на регулярки, что подходит для дампов с
    PII в значениях литералов.
    """

    def __init__(self, engine: MaskingEngine) -> None:
        self.engine = engine
        self._text_processor = TextProcessor(engine)

    def process(
        self,
        source: Path,
        destination: Path,
        encoding: str | None = None,
    ) -> None:
        self._text_processor.process(
            source=source,
            destination=destination,
            encoding=encoding,
        )

    def process_with_stats(
        self,
        source: Path,
        destination: Path,
        encoding: str | None = None,
    ) -> AnalysisResult:
        return self._text_processor.process_with_stats(
            source=source,
            destination=destination,
            encoding=encoding,
        )

    def analyze(
        self,
        source: Path,
        encoding: str | None = None,
    ) -> AnalysisResult:
        return self._text_processor.analyze(source=source, encoding=encoding)
