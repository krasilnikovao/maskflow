"""Детектор КПП (Код причины постановки на учёт).

Формат: 9 цифр AAABBBCCС, где:
  AAA — код налогового органа (3 цифры)
  BBB — причина постановки (2 буквы или 2 цифры)
  CCC — порядковый номер (3 цифры)

Пример: 773401001, 770401001
"""

import regex

from maskflow.detectors.regex_base import RegexDetector

# КПП: 9 символов, позиции 5-6 — латинские буквы ИЛИ цифры
KPP_REGEX = regex.compile(
    r"""
    (?<!\d)
    (?P<kpp>
        \d{4}               # код налогового органа (4 цифры)
        [0-9A-Z]{2}         # причина постановки (2 цифры или заглавные буквы)
        \d{3}               # порядковый номер (3 цифры)
    )
    (?!\d)
    """,
    regex.VERBOSE,
)


class KppDetector(RegexDetector):
    name = "kpp"

    def __init__(self) -> None:
        super().__init__(KPP_REGEX)
