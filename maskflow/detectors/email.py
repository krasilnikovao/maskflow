import regex

from maskflow.detectors.regex_base import RegexDetector

EMAIL_REGEX = regex.compile(
    r"""
    (?P<email>
        [a-zA-Z0-9._%+-]+@
        [a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
    )
    """,
    regex.VERBOSE,
)


class EmailDetector(RegexDetector):
    name = "email"

    def __init__(self) -> None:
        super().__init__(EMAIL_REGEX)
