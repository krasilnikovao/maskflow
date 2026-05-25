"""Детектор IP-адресов (IPv4 и IPv6).

IPv4: классический формат d.d.d.d, каждый октет 0-255.
IPv6: полная и сокращённая нотация (::1, fe80::1, 2001:db8::1).

Для IPv4 применяется постпроцессинг: проверка диапазона каждого октета
(0-255), чтобы не матчить версии (1.2.3.4.5) и даты (01.01.2024).
"""

from collections.abc import Iterable

import regex

from maskflow.core.types import Match
from maskflow.detectors.regex_base import RegexDetector

# IPv4: четыре октета через точку, граничные lookaround запрещают смежные цифры/точки
_IPV4_PATTERN = r"""
    (?<![.\d])                          # не предшествует цифра или точка
    (?P<ipv4>
        (?:25[0-5]|2[0-4]\d|[01]?\d\d?)    # октет 1
        (?:
            \.
            (?:25[0-5]|2[0-4]\d|[01]?\d\d?)  # октеты 2-4
        ){3}
    )
    (?![.\d])                           # не следует цифра или точка
"""

# IPv6: полная нотация (8 групп по 4 hex) и сокращённая (::)
# Упрощённый паттерн — покрывает большинство реальных случаев без catastrophic backtracking
_IPV6_PATTERN = r"""
    (?<![:\w])                              # не предшествует hex-символ или двоеточие
    (?P<ipv6>
        # ::1, ::, fe80::1%eth0 — сокращённые формы
        (?:[0-9A-Fa-f]{1,4}:){1,7}[0-9A-Fa-f]{1,4}     # a:b:c:d:e:f:g:h
        |(?:[0-9A-Fa-f]{1,4}:){1,7}:                    # a::
        |:(?::[0-9A-Fa-f]{1,4}){1,7}                    # ::h
        |(?:[0-9A-Fa-f]{1,4}:){1,6}:[0-9A-Fa-f]{1,4}   # a::h
        |::(?:[0-9A-Fa-f]{1,4}:){0,5}[0-9A-Fa-f]{1,4}  # ::b:c
        |::                                               # ::
    )
    (?![:\w])                               # не следует hex-символ или двоеточие
"""

IPV4_REGEX = regex.compile(_IPV4_PATTERN, regex.VERBOSE)
IPV6_REGEX = regex.compile(_IPV6_PATTERN, regex.VERBOSE)


class IpAddressDetector(RegexDetector):
    """Детектор IPv4-адресов.

    IPv6 поддерживается через отдельный IpV6Detector или путём передачи
    IPV6_REGEX в конструктор.
    """

    name = "ip_address"

    def __init__(self) -> None:
        super().__init__(IPV4_REGEX)

    def detect(self, text: str) -> Iterable[Match]:
        """Фильтрует матчи, у которых хотя бы один октет > 255 (extra safety)."""
        for match in super().detect(text):
            parts = match.value.split(".")
            if all(0 <= int(p) <= 255 for p in parts):
                yield match
