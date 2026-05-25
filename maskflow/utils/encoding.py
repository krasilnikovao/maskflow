"""Эвристика определения кодировки текстовых файлов.

Для точного определения кодировки рекомендуется установить charset-normalizer:

    pip install charset-normalizer

После этого можно заменить detect_text_encoding на:

    from charset_normalizer import from_path

    def detect_text_encoding(path: Path, **_: object) -> str:
        result = from_path(path).best()
        return str(result.encoding) if result is not None else DEFAULT_ENCODING

Без charset-normalizer используется простая побайтовая проверка. ВНИМАНИЕ:
cp1251 успешно декодирует любые однобайтовые последовательности, поэтому она
«выигрывает» всегда, когда utf-8 не подходит. Это может давать ложные
срабатывания на файлах в других 8-битных кодировках.
"""

from pathlib import Path

DEFAULT_ENCODING = "utf-8"

FALLBACK_ENCODINGS = [
    "utf-8",
    "utf-8-sig",
    "cp1251",
    "cp866",
]


def detect_text_encoding(
    path: Path,
    fallback_encodings: list[str] | None = None,
    sample_size: int = 64 * 1024,
) -> str:
    """Грубая эвристика выбора кодировки.

    Читает ТОЛЬКО первые sample_size байт (не весь файл!).

    Ограничения:
    - cp1251 декодирует любые байты — она «выигрывает» при любом
      однобайтовом содержимом, если utf-8 отказал.
    - Для точной детекции используйте charset-normalizer (см. docstring модуля).
    """
    encodings = fallback_encodings or FALLBACK_ENCODINGS

    if sample_size <= 0:
        raise ValueError("sample_size must be greater than zero")

    with path.open("rb") as file:
        sample = file.read(sample_size)

    for encoding in encodings:
        try:
            sample.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue

    return DEFAULT_ENCODING
