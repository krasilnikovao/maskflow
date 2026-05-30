"""Частичная маска: скрывает середину значения, сохраняя крайние символы.

Поведение зависит от формата значения:
  - Email:   ex***@mail.ru  (первые visible_chars символов локальной части + ***@домен)
  - Прочее:  ab***xy        (первые + последние visible_chars символов)

Режим не использует секрет и не поддерживает reversible_mapping —
частичное значение обратимо и без хранилища (домен/суффикс видны).
"""

from maskflow.core.interfaces import BaseMasker
from maskflow.storage.encrypted_mapping import EncryptedMappingStore
from maskflow.storage.entity_cache import EntityCache

_MASK_PLACEHOLDER = "***"
_DEFAULT_VISIBLE_CHARS = 2


class PartialMasker(BaseMasker):
    name = "partial"

    def __init__(
        self,
        secret: str = "",  # не используется; принимается для совместимости с MaskerFactory
        prefix: str = "",  # не используется; частичная маска не добавляет префикс
        cache: EntityCache | None = None,  # не используется
        reversible_mapping: EncryptedMappingStore | None = None,  # не используется
        visible_chars: int = _DEFAULT_VISIBLE_CHARS,
    ) -> None:
        if visible_chars < 1:
            raise ValueError("visible_chars must be at least 1")
        self._visible = visible_chars

    def mask(self, value: str) -> str:
        if not value:
            return value

        # Email: сохраняем domain, показываем только начало локальной части
        at_pos = value.find("@")
        if at_pos > 0:
            local = value[:at_pos]
            domain = value[at_pos:]  # включает '@'
            visible_prefix = local[: self._visible] if len(local) > self._visible else ""
            masked_local = visible_prefix + _MASK_PLACEHOLDER
            return masked_local + domain

        return _partial_string(value, self._visible)


def _partial_string(value: str, visible: int) -> str:
    """Возвращает первые `visible` символов + *** + последние `visible` символов.

    Если строка слишком короткая, возвращает только `***`.
    """
    if len(value) <= visible * 2:
        return _MASK_PLACEHOLDER
    return value[:visible] + _MASK_PLACEHOLDER + value[-visible:]
