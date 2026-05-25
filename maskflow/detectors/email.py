import regex

from maskflow.detectors.regex_base import RegexDetector

# Поддержка:
# - Стандартных ASCII TLD: example@mail.ru, user@company.com
# - Кириллических TLD (IDN): user@компания.рф, admin@сайт.онлайн
# - Punycode-доменов: user@xn--e1afmapc.xn--p1ai
#
# \p{L} — любая Unicode-буква (кириллица, латиница, etc.)
# Домен допускает Unicode-буквы для IDN/кириллических доменов.
EMAIL_REGEX = regex.compile(
    r"""
    (?P<email>
        # Локальная часть: ASCII-набор (RFC 5321)
        [a-zA-Z0-9._%+\-]+
        @
        # Доменная часть: поддержка ASCII и Unicode (IDN/кириллика)
        (?:
            [a-zA-Z0-9\p{L}]           # начало метки
            [a-zA-Z0-9\p{L}\-]*        # середина метки
            \.                         # разделитель
        )+
        # TLD: минимум 2 символа, только буквы (ASCII или Unicode)
        [a-zA-Z\p{L}]{2,}
    )
    """,
    regex.VERBOSE | regex.UNICODE,
)


class EmailDetector(RegexDetector):
    name = "email"

    def __init__(self) -> None:
        super().__init__(EMAIL_REGEX)
