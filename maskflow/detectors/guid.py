import regex

from maskflow.detectors.regex_base import RegexDetector

GUID_REGEX = regex.compile(
    r"""
    (?P<guid>
        [0-9a-fA-F]{8}-
        [0-9a-fA-F]{4}-
        [0-9a-fA-F]{4}-
        [0-9a-fA-F]{4}-
        [0-9a-fA-F]{12}
    )
    """,
    regex.VERBOSE,
)


class GuidDetector(RegexDetector):
    name = "guid"
    pattern = GUID_REGEX
