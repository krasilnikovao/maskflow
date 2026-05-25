"""Детектор СНИЛС (Страховой номер индивидуального лицевого счёта).

Формат: XXX-XXX-XXX YY или XXXXXXXXXXX (11 цифр).
Контрольная сумма: сумма произведений каждой цифры на её позицию (с конца).
"""

from collections.abc import Iterable

import regex

from maskflow.core.types import Match
from maskflow.detectors.regex_base import RegexDetector

# Допустимые форматы:
#   123-456-789 01  (с дефисами и пробелом перед контрольными)
#   12345678901     (11 цифр без разделителей)
SNILS_REGEX = regex.compile(
    r"""
    (?<!\d)
    (?P<snils>
        \d{3}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{2}
    )
    (?!\d)
    """,
    regex.VERBOSE,
)


def _normalize(value: str) -> str:
    """Убирает все не-цифровые символы."""
    return regex.sub(r"\D", "", value)


def is_valid_snils(value: str) -> bool:
    """Проверяет контрольную сумму СНИЛС.

    Алгоритм:
    - Взять первые 9 цифр.
    - Каждую умножить на её позицию (1..9 с начала).
    - Сумма mod 101. Если >= 100 — 0. Результат == последние 2 цифры.
    """
    digits = _normalize(value)

    if len(digits) != 11:
        return False

    # СНИЛС не может начинаться с 00
    if digits[:2] == "00":
        return False

    total = sum(int(digits[i]) * (9 - i) for i in range(9))
    remainder = total % 101
    expected = 0 if remainder >= 100 else remainder

    return expected == int(digits[9:11])


class SnilsDetector(RegexDetector):
    name = "snils"

    def __init__(self) -> None:
        super().__init__(SNILS_REGEX)

    def detect(self, text: str) -> Iterable[Match]:
        for match in super().detect(text):
            if is_valid_snils(match.value):
                yield match
