from pathlib import Path

from maskflow.services.text_masking import TextMaskingService


def test_text_masking_service_masks_text(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        """
pipeline:
  deterministic_secret: "secret"

rules:
  email:
    enabled: true
    mode: hmac
    prefix: EMAIL
""",
        encoding="utf-8",
    )

    result = TextMaskingService().mask_text(
        text="Contact: admin@example.com",
        config_path=config,
    )

    assert "admin@example.com" not in result.masked_text
    assert "EMAIL_" in result.masked_text
    assert result.matches_applied == 1
