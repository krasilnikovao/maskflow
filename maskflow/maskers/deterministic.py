import hashlib
import hmac


def pseudonymize(secret: str, value: str) -> str:
    digest = hmac.new(
        secret.encode(),
        value.encode(),
        hashlib.sha256,
    ).hexdigest()

    return digest[:16]