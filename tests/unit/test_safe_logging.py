from maskflow.utils.logging import drop_sensitive_values


def test_drop_sensitive_values_redacts_sensitive_keys() -> None:
    event = {
        "event": "test",
        "email": "admin@example.com",
        "phone": "+7 999 123-45-67",
        "inn": "7707083893",
        "guid": "550e8400-e29b-41d4-a716-446655440000",
        "safe_counter": 4,
    }

    result = drop_sensitive_values(None, "info", event)

    assert result["email"] == "[REDACTED]"
    assert result["phone"] == "[REDACTED]"
    assert result["inn"] == "[REDACTED]"
    assert result["guid"] == "[REDACTED]"
    assert result["safe_counter"] == 4


def test_drop_sensitive_values_is_case_insensitive() -> None:
    event = {
        "Email": "admin@example.com",
        "VALUE": "secret",
    }

    result = drop_sensitive_values(None, "info", event)

    assert result["Email"] == "[REDACTED]"
    assert result["VALUE"] == "[REDACTED]"
