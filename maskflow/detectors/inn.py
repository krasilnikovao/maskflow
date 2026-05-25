from collections.abc import Iterable

import regex

from maskflow.core.types import Match
from maskflow.detectors.regex_base import RegexDetector

INN_REGEX = regex.compile(
    r"""
    (?<!\d)
    (\d{10}|\d{12})
    (?!\d)
    """,
    regex.VERBOSE,
)

_WEIGHTS_10 = (2, 4, 10, 3, 5, 9, 4, 6, 8, 0)
_WEIGHTS_12_1 = (7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0)
_WEIGHTS_12_2 = (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0)


def _checksum(digits: tuple[int, ...], weights: tuple[int, ...]) -> int:
    return sum(d * w for d, w in zip(digits, weights, strict=False)) % 11 % 10


def is_valid_inn(value: str) -> bool:
    if not value.isdigit():
        return False

    digits = tuple(int(d) for d in value)

    if len(digits) == 10:
        return _checksum(digits[:10], _WEIGHTS_10) == digits[9]

    if len(digits) == 12:
        return (
            _checksum(digits[:11], _WEIGHTS_12_1) == digits[10]
            and _checksum(digits[:12], _WEIGHTS_12_2) == digits[11]
        )

    return False


class InnDetector(RegexDetector):
    name = "inn"

    def __init__(self) -> None:
        super().__init__(INN_REGEX)

    def detect(self, text: str) -> Iterable[Match]:
        for match in super().detect(text):
            if is_valid_inn(match.value):
                yield match
