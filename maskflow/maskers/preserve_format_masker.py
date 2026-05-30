"""Формат-сохраняющая маскировка.

Каждый символ заменяется символом того же класса:
  - цифра        → другая цифра
  - латиница     → латиница того же регистра
  - кириллица    → кириллица того же регистра
  - разделители  → без изменений (пробел, дефис, скобки, точки и т.п.)

Замена детерминирована: одно и то же значение всегда даёт один и тот же результат,
что обеспечивает стабильность между запусками при одном и том же секрете.

Пример:
  7707083893  →  3841259607
  +7 (999) 123-45-67  →  +7 (412) 853-91-24
"""

import hashlib
import hmac as _hmac

from maskflow.core.interfaces import BaseMasker
from maskflow.storage.encrypted_mapping import EncryptedMappingStore
from maskflow.storage.entity_cache import EntityCache

_DIGITS = "0123456789"
_LATIN_LOWER = "abcdefghijklmnopqrstuvwxyz"
_LATIN_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# Кириллица без Ё/ё для единообразия (33-я буква создаёт смещение в ord-арифметике)
_CYRILLIC_LOWER = "абвгдежзийклмнопрстуфхцчшщъыьэюя"
_CYRILLIC_UPPER = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"

# Размер блока HMAC-дайджеста
_DIGEST_SIZE = 32


class PreserveFormatMasker(BaseMasker):
    name = "preserve_format"

    def __init__(
        self,
        secret: str,
        prefix: str = "",  # не используется: вывод должен выглядеть как оригинал
        cache: EntityCache | None = None,  # не используется
        reversible_mapping: EncryptedMappingStore | None = None,  # не используется
    ) -> None:
        if not secret:
            raise ValueError("PreserveFormatMasker secret must not be empty")
        self._secret = secret.encode("utf-8")

    def mask(self, value: str) -> str:
        if not value:
            return value

        key_stream = _derive_key_stream(self._secret, value, len(value))

        result: list[str] = []
        for i, char in enumerate(value):
            b = key_stream[i]
            if char.isdigit():
                result.append(_DIGITS[b % 10])
            elif char in _LATIN_LOWER:
                result.append(_LATIN_LOWER[b % 26])
            elif char in _LATIN_UPPER:
                result.append(_LATIN_UPPER[b % 26])
            elif char in _CYRILLIC_LOWER:
                result.append(_CYRILLIC_LOWER[b % len(_CYRILLIC_LOWER)])
            elif char in _CYRILLIC_UPPER:
                result.append(_CYRILLIC_UPPER[b % len(_CYRILLIC_UPPER)])
            else:
                # Разделители, пробелы, скобки — сохраняем
                result.append(char)

        return "".join(result)


def _derive_key_stream(secret: bytes, value: str, length: int) -> bytes:
    """Генерирует детерминированный поток байт нужной длины через HMAC-SHA256.

    Для значений длиннее 32 символов расширяет поток итеративным хэшированием.
    """
    chunks: list[bytes] = []
    needed = length
    counter = 0

    while needed > 0:
        msg = f"{counter}:{value}".encode()
        chunk = _hmac.new(secret, msg, hashlib.sha256).digest()
        chunks.append(chunk)
        needed -= _DIGEST_SIZE
        counter += 1

    return b"".join(chunks)[:length]
