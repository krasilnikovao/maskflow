import hashlib
import hmac

from maskflow.core.interfaces import BaseMasker
from maskflow.storage.encrypted_mapping import EncryptedMappingStore
from maskflow.storage.entity_cache import EntityCache

DEFAULT_HASH_LENGTH = 24  # hex chars = 96 bits — снижает риск коллизий на крупных датасетах
MIN_HASH_LENGTH = 8
MAX_HASH_LENGTH = 64


class HmacMasker(BaseMasker):
    name = "hmac"

    def __init__(
        self,
        secret: str,
        prefix: str = "MASK",
        cache: EntityCache | None = None,
        reversible_mapping: EncryptedMappingStore | None = None,
        hash_length: int = DEFAULT_HASH_LENGTH,
    ) -> None:
        if not secret:
            raise ValueError("HMAC secret must not be empty")

        if not (MIN_HASH_LENGTH <= hash_length <= MAX_HASH_LENGTH):
            raise ValueError(
                f"hash_length must be between {MIN_HASH_LENGTH} and {MAX_HASH_LENGTH}"
            )

        self._secret = secret.encode("utf-8")
        self._prefix = prefix
        self._cache = cache
        self._reversible_mapping = reversible_mapping
        self._hash_length = hash_length

    def mask(self, value: str) -> str:
        digest = hmac.new(
            self._secret,
            value.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        cache_key = digest

        if self._cache is not None:
            cached = self._cache.get(cache_key)

            if cached is not None:
                if self._reversible_mapping is not None:
                    self._reversible_mapping.set(cached, value)

                return cached

        masked = f"{self._prefix}_{digest[: self._hash_length]}"

        if self._reversible_mapping is not None:
            self._reversible_mapping.set(masked, value)

        if self._cache is not None:
            self._cache.set(cache_key, masked)

        return masked
