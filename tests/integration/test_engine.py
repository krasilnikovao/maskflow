from maskflow.core.engine import MaskingEngine
from maskflow.detectors.email import EmailDetector
from maskflow.maskers.hmac_masker import HmacMasker


def test_email_masking() -> None:
    engine = MaskingEngine(
        detectors=[EmailDetector()],
        maskers={
            "email": HmacMasker(secret="secret", prefix="EMAIL"),
        },
    )

    source = "Contact me: admin@example.com"
    result = engine.process_text(source)

    assert "admin@example.com" not in result
    assert "EMAIL_" in result
