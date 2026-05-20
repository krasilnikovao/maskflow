from pathlib import Path

from maskflow.core.engine import MaskingEngine
from maskflow.detectors.email import EmailDetector
from maskflow.formats.sql import SqlProcessor
from maskflow.maskers.hmac_masker import HmacMasker


def test_sql_processor_masks_email_in_insert(tmp_path: Path) -> None:
    source = tmp_path / "dump.sql"
    destination = tmp_path / "masked.sql"

    source.write_text(
        """
INSERT INTO users (id, email)
VALUES (1, 'admin@example.com');
""",
        encoding="utf-8",
    )

    engine = MaskingEngine(
        detectors=[EmailDetector()],
        maskers={
            "email": HmacMasker(secret="secret", prefix="EMAIL"),
        },
    )

    processor = SqlProcessor(engine)

    processor.process(
        source=source,
        destination=destination,
    )

    masked = destination.read_text(encoding="utf-8")

    assert "admin@example.com" not in masked
    assert "EMAIL_" in masked
    assert "INSERT INTO users" in masked


def test_sql_processor_analyze_returns_statistics(tmp_path: Path) -> None:
    source = tmp_path / "dump.sql"

    source.write_text(
        """
INSERT INTO users (id, email)
VALUES (1, 'admin@example.com');
""",
        encoding="utf-8",
    )

    engine = MaskingEngine(
        detectors=[EmailDetector()],
        maskers={
            "email": HmacMasker(secret="secret", prefix="EMAIL"),
        },
    )

    processor = SqlProcessor(engine)

    analysis = processor.analyze(source)

    assert analysis.matches_found == 1
    assert analysis.matches_applied == 1
    assert analysis.detector_counts == {"email": 1}


def test_sql_processor_handles_multiline_dump(tmp_path: Path) -> None:
    source = tmp_path / "dump.sql"
    destination = tmp_path / "masked.sql"

    source.write_text(
        """
BEGIN;

INSERT INTO users (id, email)
VALUES
  (1, 'admin@example.com'),
  (2, 'user@example.com');

COMMIT;
""",
        encoding="utf-8",
    )

    engine = MaskingEngine(
        detectors=[EmailDetector()],
        maskers={
            "email": HmacMasker(secret="secret", prefix="EMAIL"),
        },
    )

    processor = SqlProcessor(engine)

    processor.process(
        source=source,
        destination=destination,
    )

    masked = destination.read_text(encoding="utf-8")

    assert "admin@example.com" not in masked
    assert "user@example.com" not in masked
    assert masked.count("EMAIL_") == 2
    assert "BEGIN;" in masked
    assert "COMMIT;" in masked
