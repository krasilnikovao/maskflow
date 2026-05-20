from pathlib import Path

import pytest

from maskflow.core.streaming import stream_text_file


def test_stream_text_file_reads_chunks(tmp_path: Path) -> None:
    source = tmp_path / "sample.txt"
    source.write_text("abcdef", encoding="utf-8")

    chunks = list(stream_text_file(source, chunk_size=2))

    assert chunks == ["ab", "cd", "ef"]


def test_stream_text_file_rejects_invalid_chunk_size(tmp_path: Path) -> None:
    source = tmp_path / "sample.txt"
    source.write_text("abcdef", encoding="utf-8")

    with pytest.raises(ValueError, match="chunk_size must be greater than zero"):
        list(stream_text_file(source, chunk_size=0))


def test_stream_text_file_rejects_missing_file(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        list(stream_text_file(missing_file))


def test_stream_text_file_rejects_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Path is not a file"):
        list(stream_text_file(tmp_path))


def test_stream_text_file_reads_unicode(tmp_path: Path) -> None:
    source = tmp_path / "unicode.txt"
    expected = "Иванов Иван Иванович\nООО Ромашка"

    source.write_text(expected, encoding="utf-8", newline="\n")

    chunks = list(stream_text_file(source, chunk_size=10))

    assert "".join(chunks) == expected
