"""Детектор ОГРН / ОГРНИП.

ОГРН  — 13 цифр (юридические лица)
ОГРНИП — 15 цифр (индивидуальные предприниматели)

Контрольная сумма:
  ОГРН:   (N - floor(N/11)*11) mod 10, где N = первые 12 цифр
  ОГРНИП: (N - floor(N/13)*13) mod 10, где N = первые 14 цифр
"""

from collections.abc import Iterable

import regex

from maskflow.core.types import Match
from maskflow.detectors.regex_base import RegexDetector

OGRN_REGEX = regex.compile(
    r"""
    (?<!\d)
    (?P<ogrn>
        \d{13}          # ОГРН (13 цифр)
        |
        \d{15}          # ОГРНИП (15 цифр)
    )
    (?!\d)
    """,
    regex.VERBOSE,
)


def is_valid_ogrn(value: str) -> bool:
    """Проверяет контрольную сумму ОГРН или ОГРНИП."""
    if not value.isdigit():
        return False

    length = len(value)

    if length == 13:
        base = int(value[:12])
        expected = (base - (base // 11) * 11) % 10
        return expected == int(value[12])

    if length == 15:
        base = int(value[:14])
        expected = (base - (base // 13) * 13) % 10
        return expected == int(value[14])

    return False


class OgrnDetector(RegexDetector):
    name = "ogrn"

    def __init__(self) -> None:
        super().__init__(OGRN_REGEX)

    def detect(self, text: str) -> Iterable[Match]:
        for match in super().detect(text):
            if is_valid_ogrn(match.value):
                yield match
