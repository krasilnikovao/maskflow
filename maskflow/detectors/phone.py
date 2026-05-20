import regex

from maskflow.detectors.regex_base import RegexDetector

PHONE_REGEX = regex.compile(
    r"""
    (?P<phone>
        (?:\+7|8)
        [\s\-(]*
        \d{3}
        [\s\-)]*
        \d{3}
        [\s\-]*
        \d{2}
        [\s\-]*
        \d{2}
    )
    """,
    regex.VERBOSE,
)


class PhoneDetector(RegexDetector):
    name = "phone"
    pattern = PHONE_REGEX
