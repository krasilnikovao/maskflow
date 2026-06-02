from collections.abc import Iterable

import regex

from maskflow.core.types import Match
from maskflow.detectors.regex_base import RegexDetector

DOCUMENT_CODE_REGEX = regex.compile(
    r"""
    (?ix)
    (?:\b(?:код|номер|document|doc|id)\b|[№#])
    \s*[:=]?\s*
    (?P<document_code>
        (?=[\p{L}\d_./-]{6,}\b)
        (?=[\p{L}\d_./-]*\p{L})
        (?=[\p{L}\d_./-]*\d)
        [\p{L}\d][\p{L}\d_./-]{5,}
    )
    """,
    regex.VERBOSE,
)


class DocumentCodeDetector(RegexDetector):
    name = "document_code"

    def __init__(self) -> None:
        super().__init__(DOCUMENT_CODE_REGEX)

    def detect(self, text: str) -> Iterable[Match]:
        for match in self._pattern.finditer(text, timeout=self._timeout):
            start, end = match.span(self.name)
            yield Match(
                detector=self.name,
                start=start,
                end=end,
                value=match.group(self.name),
            )
