import pytest

from maskflow.maskers.hmac_masker import HmacMasker


class FakeCache:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def set(self, key: str, value: str) -> None:
        self.values[key] = value


class FakeMapping:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def set(self, key: str, value: str) -> None:
        self.values[key] = value


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


def test_hmac_masker_writes_reversible_mapping_for_cached_values() -> None:
    cache = FakeCache()
    mapping = FakeMapping()
    masker = HmacMasker(
        secret="secret",
        prefix="EMAIL",
        cache=cache,  # type: ignore[arg-type]
        reversible_mapping=mapping,  # type: ignore[arg-type]
    )

    first = masker.mask("admin@example.com")
    mapping.values.clear()

    second = masker.mask("admin@example.com")

    assert second == first
    assert mapping.values == {first: "admin@example.com"}
