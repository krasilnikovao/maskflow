import copy
from collections.abc import Iterable

import regex

from maskflow.core.interfaces import BaseDetector
from maskflow.core.types import Match
from maskflow.security.regex_policy import (
    DEFAULT_REGEX_TIMEOUT_SECONDS,
    validate_regex_timeout,
)


class RegexDetector(BaseDetector):
    pattern: regex.Pattern[str]
    timeout_seconds: float = DEFAULT_REGEX_TIMEOUT_SECONDS

    def detect(self, text: str) -> Iterable[Match]:
        timeout_seconds = validate_regex_timeout(self.timeout_seconds)

        for match in self.pattern.finditer(
            text,
            timeout=timeout_seconds,
        ):
            yield Match(
                detector=self.name,
                start=match.start(),
                end=match.end(),
                value=match.group(),
            )

    def with_timeout(self, timeout_seconds: float) -> "RegexDetector":
        clone = copy.copy(self)
        clone.timeout_seconds = validate_regex_timeout(timeout_seconds)
        return clone
