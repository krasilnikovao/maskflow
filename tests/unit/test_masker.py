"""Tests for HmacMasker.

The legacy maskflow.maskers.deterministic.pseudonymize() function has been
removed. All deterministic masking now goes through HmacMasker.
"""

import pytest

from maskflow.maskers.hmac_masker import HmacMasker


def test_hmac_masker_is_deterministic() -> None:
    masker = HmacMasker(secret="test-secret", prefix="MASK")
    assert masker.mask("same-value") == masker.mask("same-value")


def test_hmac_masker_different_values_produce_different_masks() -> None:
    masker = HmacMasker(secret="test-secret", prefix="MASK")
    assert masker.mask("value-a") != masker.mask("value-b")


def test_hmac_masker_different_secrets_produce_different_masks() -> None:
    masker_a = HmacMasker(secret="secret-a", prefix="MASK")
    masker_b = HmacMasker(secret="secret-b", prefix="MASK")
    assert masker_a.mask("same-value") != masker_b.mask("same-value")


def test_hmac_masker_prefix_applied() -> None:
    masker = HmacMasker(secret="test-secret", prefix="EMAIL")
    result = masker.mask("test@example.com")
    assert result.startswith("EMAIL_")


def test_hmac_masker_empty_secret_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        HmacMasker(secret="", prefix="MASK")


def test_hmac_masker_invalid_hash_length_raises() -> None:
    with pytest.raises(ValueError, match="hash_length"):
        HmacMasker(secret="secret", prefix="MASK", hash_length=3)


@pytest.mark.parametrize(
    "value",
    [
        "ivanov@company.ru",
        "+7 (495) 123-45-67",
        "7707083893",
        "Иванов Иван Иванович",
        "ООО Ромашка",
        "",
        " ",
        "a" * 1000,
    ],
)
def test_hmac_masker_handles_various_inputs(value: str) -> None:
    masker = HmacMasker(secret="test-secret", prefix="MASK")
    result = masker.mask(value)
    # Must always return a deterministic, non-empty string
    assert isinstance(result, str)
    assert len(result) > 0
    assert result == masker.mask(value)
