from pathlib import Path

import pytest

from maskflow.utils.atomic import atomic_write_binary_via_temp, atomic_write_text


def test_atomic_write_text_writes_content(tmp_path: Path) -> None:
    destination = tmp_path / "output.txt"

    atomic_write_text(
        destination=destination,
        content="masked content",
    )

    assert destination.read_text(encoding="utf-8") == "masked content"


def test_atomic_write_text_replaces_existing_file(tmp_path: Path) -> None:
    destination = tmp_path / "output.txt"
    destination.write_text("old content", encoding="utf-8")

    atomic_write_text(
        destination=destination,
        content="new content",
    )

    assert destination.read_text(encoding="utf-8") == "new content"


def test_atomic_write_binary_via_temp_writes_file(tmp_path: Path) -> None:
    destination = tmp_path / "output.bin"

    def writer(temp_path: Path) -> None:
        temp_path.write_bytes(b"masked")

    atomic_write_binary_via_temp(
        destination=destination,
        writer=writer,
    )

    assert destination.read_bytes() == b"masked"


def test_atomic_write_binary_via_temp_cleans_up_on_failure(tmp_path: Path) -> None:
    destination = tmp_path / "output.bin"

    def writer(temp_path: Path) -> None:
        temp_path.write_bytes(b"partial")
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        atomic_write_binary_via_temp(
            destination=destination,
            writer=writer,
        )

    assert not destination.exists()
    assert list(tmp_path.glob("*.tmp")) == []
