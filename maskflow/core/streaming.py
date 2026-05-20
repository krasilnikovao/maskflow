from collections.abc import Generator
from pathlib import Path

DEFAULT_CHUNK_SIZE = 1024 * 1024


def stream_text_file(
    path: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    encoding: str = "utf-8",
    errors: str = "replace",
) -> Generator[str, None, None]:
    """Стриминговое чтение текстового файла блоками.

    По умолчанию ``errors="replace"`` — если в файле встретятся байты, не
    декодируемые в выбранной кодировке, они заменяются на U+FFFD вместо падения.
    Маскирование от такого не страдает, но для строгих сценариев передавайте
    ``errors="strict"``.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(file_path)

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    with file_path.open(
        encoding=encoding,
        errors=errors,
        newline="",
    ) as file:
        while chunk := file.read(chunk_size):
            yield chunk
