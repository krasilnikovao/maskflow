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
    Внимание: cp1251 декодирует любые байты, поэтому она "выигрывает" всегда,
    если utf-8 не подходит. Для точной детекции подключайте charset-normalizer.
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
