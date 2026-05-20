import pytest

from maskflow.maskers.hmac_masker import HmacMasker


def test_hmac_masker_is_deterministic() -> None:
    masker = HmacMasker(secret="secret", prefix="EMAIL")

    first = masker.mask("admin@example.com")
    second = masker.mask("admin@example.com")

    assert first == second
    assert first.startswith("EMAIL_")


def test_hmac_masker_changes_for_different_values() -> None:
    masker = HmacMasker(secret="secret", prefix="EMAIL")

    first = masker.mask("admin@example.com")
    second = masker.mask("user@example.com")

    assert first != second


def test_hmac_masker_rejects_empty_secret() -> None:
    with pytest.raises(ValueError, match="HMAC secret must not be empty"):
        HmacMasker(secret="")
