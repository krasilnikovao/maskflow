"""Tests for HmacMasker, PartialMasker, PreserveFormatMasker, RedactMasker."""

import pytest

from maskflow.maskers.hmac_masker import HmacMasker
from maskflow.maskers.partial_masker import PartialMasker
from maskflow.maskers.preserve_format_masker import PreserveFormatMasker
from maskflow.maskers.redact_masker import RedactMasker


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
    assert isinstance(result, str)
    assert len(result) > 0
    assert result == masker.mask(value)


# ---------------------------------------------------------------------------
# PartialMasker
# ---------------------------------------------------------------------------


def test_partial_masker_email() -> None:
    masker = PartialMasker()
    assert masker.mask("example@mail.ru") == "ex***@mail.ru"


def test_partial_masker_email_preserves_domain() -> None:
    masker = PartialMasker()
    result = masker.mask("user@example.com")
    assert result.endswith("@example.com")


def test_partial_masker_generic_long() -> None:
    masker = PartialMasker()
    assert masker.mask("1234567890") == "12***90"


def test_partial_masker_short_returns_placeholder() -> None:
    masker = PartialMasker()
    assert masker.mask("ab") == "***"


def test_partial_masker_empty() -> None:
    masker = PartialMasker()
    assert masker.mask("") == ""


def test_partial_masker_cyrillic() -> None:
    masker = PartialMasker()
    result = masker.mask("Иванов Иван")
    assert result.startswith("Ив")
    assert "***" in result


def test_partial_masker_custom_visible_chars() -> None:
    masker = PartialMasker(visible_chars=3)
    assert masker.mask("1234567890") == "123***890"


def test_partial_masker_invalid_visible_chars_raises() -> None:
    with pytest.raises(ValueError):
        PartialMasker(visible_chars=0)


# ---------------------------------------------------------------------------
# PreserveFormatMasker
# ---------------------------------------------------------------------------


def test_preserve_format_masker_length() -> None:
    masker = PreserveFormatMasker(secret="test-secret")
    value = "7707083893"
    assert len(masker.mask(value)) == len(value)


def test_preserve_format_masker_digits_stay_digits() -> None:
    masker = PreserveFormatMasker(secret="test-secret")
    assert masker.mask("7707083893").isdigit()


def test_preserve_format_masker_deterministic() -> None:
    masker = PreserveFormatMasker(secret="test-secret")
    assert masker.mask("7707083893") == masker.mask("7707083893")


def test_preserve_format_masker_different_secrets_differ() -> None:
    m1 = PreserveFormatMasker(secret="secret-a")
    m2 = PreserveFormatMasker(secret="secret-b")
    assert m1.mask("7707083893") != m2.mask("7707083893")


def test_preserve_format_masker_separators_preserved() -> None:
    masker = PreserveFormatMasker(secret="test-secret")
    value = "+7 (999) 123-45-67"
    result = masker.mask(value)
    assert len(result) == len(value)
    for orig, masked in zip(value, result, strict=True):
        if not orig.isdigit():
            assert orig == masked


def test_preserve_format_masker_latin_case_preserved() -> None:
    masker = PreserveFormatMasker(secret="test-secret")
    value = "AbCdEf"
    result = masker.mask(value)
    for orig, masked in zip(value, result, strict=True):
        assert orig.isupper() == masked.isupper()


def test_preserve_format_masker_long_value() -> None:
    masker = PreserveFormatMasker(secret="test-secret")
    value = "1234567890" * 5
    result = masker.mask(value)
    assert len(result) == len(value)
    assert result.isdigit()


def test_preserve_format_masker_empty_secret_raises() -> None:
    with pytest.raises(ValueError):
        PreserveFormatMasker(secret="")


# ---------------------------------------------------------------------------
# RedactMasker
# ---------------------------------------------------------------------------


def test_redact_masker_with_prefix() -> None:
    masker = RedactMasker(prefix="EMAIL")
    assert masker.mask("user@example.com") == "EMAIL_REDACTED"


def test_redact_masker_without_prefix() -> None:
    masker = RedactMasker()
    assert masker.mask("user@example.com") == "[REDACTED]"


def test_redact_masker_always_same_token() -> None:
    masker = RedactMasker(prefix="PHONE")
    assert masker.mask("+79991234567") == masker.mask("+74951234567")


def test_redact_masker_empty_value() -> None:
    masker = RedactMasker(prefix="INN")
    assert masker.mask("") == "INN_REDACTED"
