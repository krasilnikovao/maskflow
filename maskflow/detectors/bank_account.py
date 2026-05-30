import regex

from maskflow.detectors.regex_base import RegexDetector

BANK_ACCOUNT_REGEX = regex.compile(
    r"""
    (?<!\d)
    (?P<bank_account>\d{20})
    (?!\d)
    """,
    regex.VERBOSE,
)


class BankAccountDetector(RegexDetector):
    name = "bank_account"

    def __init__(self) -> None:
        super().__init__(BANK_ACCOUNT_REGEX)
