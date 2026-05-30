import json
from pathlib import Path
from unittest.mock import patch

import pytest

from maskflow.core.engine import MaskingEngine
from maskflow.detectors.email import EmailDetector
from maskflow.formats.json import _MAX_JSON_SIZE_BYTES, JsonProcessor
from maskflow.maskers.hmac_masker import HmacMasker


def build_engine() -> MaskingEngine:
    return MaskingEngine(
        detectors=[EmailDetector()],
        maskers={
            "email": HmacMasker(
                secret="secret",
                prefix="EMAIL",
            ),
        },
    )


def test_json_processor_masks_nested_object(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    destination = tmp_path / "masked.json"

    source.write_text(
        json.dumps(
            {
                "user": {
                    "email": "admin@example.com",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    processor = JsonProcessor(build_engine())
    processor.process(source, destination)

    payload = json.loads(destination.read_text(encoding="utf-8"))

    assert payload["user"]["email"].startswith("EMAIL_")
    assert payload["user"]["email"] != "admin@example.com"


def test_json_processor_masks_arrays(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    destination = tmp_path / "masked.json"

    source.write_text(
        json.dumps(
            {
                "emails": [
                    "admin@example.com",
                    "user@example.com",
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    processor = JsonProcessor(build_engine())
    processor.process(source, destination)

    payload = json.loads(destination.read_text(encoding="utf-8"))

    assert payload["emails"][0].startswith("EMAIL_")
    assert payload["emails"][1].startswith("EMAIL_")
    assert "admin@example.com" not in destination.read_text(encoding="utf-8")


def test_json_processor_preserves_unicode(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    destination = tmp_path / "masked.json"

    source.write_text(
        json.dumps(
            {
                "name": "Иван",
                "email": "admin@example.com",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    processor = JsonProcessor(build_engine())
    processor.process(source, destination)

    content = destination.read_text(encoding="utf-8")
    payload = json.loads(content)

    assert payload["name"] == "Иван"
    assert payload["email"].startswith("EMAIL_")
    assert "admin@example.com" not in content


def test_json_processor_analyze_returns_statistics(tmp_path: Path) -> None:
    source = tmp_path / "source.json"

    source.write_text(
        json.dumps(
            {
                "email": "admin@example.com",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    processor = JsonProcessor(build_engine())

    analysis = processor.analyze(source)

    assert analysis.matches_found == 1
    assert analysis.matches_applied == 1
    assert analysis.matches_skipped == 0
    assert analysis.detector_counts == {"email": 1}


def test_json_processor_rejects_oversized_file(tmp_path: Path) -> None:
    """JSON-файл крупнее лимита должен немедленно вызывать ValueError."""
    source = tmp_path / "big.json"
    destination = tmp_path / "masked.json"

    source.write_text('{"email": "a@b.com"}', encoding="utf-8")

    processor = JsonProcessor(build_engine())

    # Подменяем размер файла, чтобы не создавать реальный 100 MB файл в тесте
    oversized = _MAX_JSON_SIZE_BYTES + 1
    with patch("pathlib.Path.stat") as mock_stat:
        mock_stat.return_value.st_size = oversized
        with pytest.raises(ValueError, match="too large"):
            processor.process(source, destination)


def test_json_processor_preserves_non_string_values(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    destination = tmp_path / "masked.json"

    source.write_text(
        json.dumps(
            {
                "id": 1,
                "active": True,
                "score": 12.5,
                "email": "admin@example.com",
                "empty": None,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    processor = JsonProcessor(build_engine())
    processor.process(source, destination)

    payload = json.loads(destination.read_text(encoding="utf-8"))

    assert payload["id"] == 1
    assert payload["active"] is True
    assert payload["score"] == 12.5
    assert payload["empty"] is None
    assert payload["email"].startswith("EMAIL_")
