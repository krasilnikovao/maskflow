"""Детектор URL/URI.

Поддерживаемые схемы: http, https, ftp, ftps.
Поддержка:
  - IPv4 в URL: http://192.168.1.1/path
  - Кириллические домены (IDN): http://пример.рф/страница
  - Пути, query-параметры, фрагменты
  - Порты: http://host:8080/path
  - Базовая аутентификация: http://user:pass@host/

Не матчит:
  - Просто доменные имена без схемы (используйте отдельный DomainDetector)
"""

import regex

from maskflow.detectors.regex_base import RegexDetector

# Допустимые символы метки домена: латиница, Unicode-буквы (кириллица), цифры, дефис
_LABEL = r"[a-zA-Z0-9\p{L}](?:[a-zA-Z0-9\p{L}\-]*[a-zA-Z0-9\p{L}])?"

URL_REGEX = regex.compile(
    r"""
    (?P<url>
        # Схема
        (?:https?|ftps?)://

        # Опциональная basic-auth: user:pass@
        (?:[a-zA-Z0-9._~%+\-]+(?::[a-zA-Z0-9._~%+\-]*)?@)?

        # Хост — домен или IPv4
        (?:
            (?:\d{1,3}\.){3}\d{1,3}        # IPv4
            |
            """ + _LABEL + r"""(?:\.""" + _LABEL + r""")+    # домен (с поддержкой Unicode)
        )

        # Порт
        (?::\d{1,5})?

        # Путь, query, fragment (жадный, но не жрёт пробелы и закрывающие скобки)
        (?:/[^\s<>"')\]]*)?
    )
    """,
    regex.VERBOSE | regex.UNICODE,
)


class UrlDetector(RegexDetector):
    name = "url"

    def __init__(self) -> None:
        super().__init__(URL_REGEX)
