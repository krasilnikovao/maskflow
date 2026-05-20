from maskflow.maskers.deterministic import pseudonymize


def test_pseudonymize_is_deterministic() -> None:
    assert pseudonymize("secret", "value") == pseudonymize("secret", "value")
