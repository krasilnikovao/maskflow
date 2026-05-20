DEFAULT_REGEX_TIMEOUT_SECONDS = 1.0


def validate_regex_timeout(timeout_seconds: float) -> float:
    if timeout_seconds <= 0:
        raise ValueError("regex timeout must be greater than zero")

    if timeout_seconds > 10:
        raise ValueError("regex timeout must not exceed 10 seconds")

    return timeout_seconds
