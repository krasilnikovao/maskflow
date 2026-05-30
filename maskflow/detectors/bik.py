import regex

from maskflow.detectors.regex_base import RegexDetector

BIK_REGEX = regex.compile(
    r"""
    (?<!\d)
    (?P<bik>0[0-9]{8})
    (?!\d)
    """,
    regex.VERBOSE,
)


class BikDetector(RegexDetector):
    name = "bik"

    def __init__(self) -> None:
        super().__init__(BIK_REGEX)
