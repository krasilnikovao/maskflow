from pathlib import Path

import pytest

from maskflow.utils.encoding import detect_text_encoding


def test_detect_text_encoding_detects_utf8(tmp_path: Path) -> None:
    source = tmp_path / "utf8.txt"
    source.write_text("Иван admin@example.com", encoding="utf-8")

    assert detect_text_encoding(source) == "utf-8"


def test_detect_text_encoding_detects_utf8_sig(tmp_path: Path) -> None:
    source = tmp_path / "utf8_sig.txt"
    source.write_text("Иван admin@example.com", encoding="utf-8-sig")

    assert detect_text_encoding(source) in {"utf-8", "utf-8-sig"}


def test_detect_text_encoding_detects_cp1251(tmp_path: Path) -> None:
    source = tmp_path / "cp1251.txt"
    source.write_text("Иван admin@example.com", encoding="cp1251")

    assert detect_text_encoding(source) == "cp1251"


def test_detect_text_encoding_detects_cp866(tmp_path: Path) -> None:
    source = tmp_path / "cp866.txt"
    source.write_text("Иван admin@example.com", encoding="cp866")

    assert detect_text_encoding(source) in {"cp1251", "cp866"}


def test_detect_text_encoding_rejects_invalid_sample_size(tmp_path: Path) -> None:
    source = tmp_path / "sample.txt"
    source.write_text("data", encoding="utf-8")

    with pytest.raises(ValueError, match="sample_size must be greater than zero"):
        detect_text_encoding(source, sample_size=0)
