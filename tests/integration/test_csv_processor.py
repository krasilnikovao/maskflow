from pathlib import Path

from maskflow.core.engine import MaskingEngine
from maskflow.detectors.email import EmailDetector
from maskflow.formats.csv import CsvProcessor
from maskflow.maskers.hmac_masker import HmacMasker


def test_csv_processor_masks_email(tmp_path: Path) -> None:
    source = tmp_path / "data.csv"
    destination = tmp_path / "masked.csv"

    source.write_text(
        "id,email\n1,admin@example.com\n",
        encoding="utf-8",
    )

    engine = MaskingEngine(
        detectors=[EmailDetector()],
        maskers={
            "email": HmacMasker(
                secret="secret",
                prefix="EMAIL",
            ),
        },
    )

    processor = CsvProcessor(engine)

    processor.process(
        source=source,
        destination=destination,
    )

    masked = destination.read_text(encoding="utf-8")

    assert "admin@example.com" not in masked
    assert "EMAIL_" in masked
    assert "id,email" in masked


def test_csv_processor_preserves_quoted_fields(tmp_path: Path) -> None:
    source = tmp_path / "quoted.csv"
    destination = tmp_path / "masked.csv"

    source.write_text(
        'id,comment\n1,"Contact: admin@example.com"\n',
        encoding="utf-8",
    )

    engine = MaskingEngine(
        detectors=[EmailDetector()],
        maskers={
            "email": HmacMasker(
                secret="secret",
                prefix="EMAIL",
            ),
        },
    )

    processor = CsvProcessor(engine)

    processor.process(
        source=source,
        destination=destination,
    )

    masked = destination.read_text(encoding="utf-8")

    assert "Contact: EMAIL_" in masked
    assert "admin@example.com" not in masked


def test_csv_processor_supports_semicolon_delimiter(tmp_path: Path) -> None:
    source = tmp_path / "semicolon.csv"
    destination = tmp_path / "masked.csv"

    source.write_text(
        "id;email\n1;admin@example.com\n",
        encoding="utf-8",
    )

    engine = MaskingEngine(
        detectors=[EmailDetector()],
        maskers={
            "email": HmacMasker(
                secret="secret",
                prefix="EMAIL",
            ),
        },
    )

    processor = CsvProcessor(engine)

    processor.process(
        source=source,
        destination=destination,
        delimiter=";",
    )

    masked = destination.read_text(encoding="utf-8")

    assert "admin@example.com" not in masked
    assert "EMAIL_" in masked
    assert "id;email" in masked


def test_csv_processor_analyze_returns_statistics(tmp_path: Path) -> None:
    source = tmp_path / "stats.csv"

    source.write_text(
        "id,email\n1,admin@example.com\n",
        encoding="utf-8",
    )

    engine = MaskingEngine(
        detectors=[EmailDetector()],
        maskers={
            "email": HmacMasker(
                secret="secret",
                prefix="EMAIL",
            ),
        },
    )

    processor = CsvProcessor(engine)

    analysis = processor.analyze(source)

    assert analysis.matches_found == 1
    assert analysis.matches_applied == 1
    assert analysis.matches_skipped == 0
    assert analysis.detector_counts == {"email": 1}


def test_csv_processor_preserves_unicode(tmp_path: Path) -> None:
    source = tmp_path / "unicode.csv"
    destination = tmp_path / "masked.csv"

    source.write_text(
        "имя,email\nИван,admin@example.com\n",
        encoding="utf-8",
    )

    engine = MaskingEngine(
        detectors=[EmailDetector()],
        maskers={
            "email": HmacMasker(
                secret="secret",
                prefix="EMAIL",
            ),
        },
    )

    processor = CsvProcessor(engine)

    processor.process(
        source=source,
        destination=destination,
    )

    masked = destination.read_text(encoding="utf-8")

    assert "имя" in masked
    assert "Иван" in masked
    assert "admin@example.com" not in masked
