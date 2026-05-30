"""Полное замещение (redact): заменяет значение фиксированным токеном.

Если задан prefix — результат: PREFIX_REDACTED
Если prefix пустой — результат: [REDACTED]

Быстрый и необратимый режим; не требует секрета, кэша или хранилища.
"""

from maskflow.core.interfaces import BaseMasker
from maskflow.storage.encrypted_mapping import EncryptedMappingStore
from maskflow.storage.entity_cache import EntityCache

_FALLBACK_TOKEN = "[REDACTED]"


class RedactMasker(BaseMasker):
    name = "redact"

    def __init__(
        self,
        secret: str = "",  # не используется; принимается для совместимости с MaskerFactory
        prefix: str = "",
        cache: EntityCache | None = None,  # не используется
        reversible_mapping: EncryptedMappingStore | None = None,  # не используется
    ) -> None:
        self._token = f"{prefix}_REDACTED" if prefix else _FALLBACK_TOKEN

    def mask(self, value: str) -> str:
        return self._token
