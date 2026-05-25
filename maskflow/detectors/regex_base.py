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
    """Base class for regex-driven detectors.

    Subclasses must:
    - Declare ``name: ClassVar[str]`` at class level.
    - Call ``super().__init__(pattern)`` (optionally passing ``timeout_seconds``).

    Marked as an intermediate abstract base so ``BaseDetector.__init_subclass__``
    does not enforce the ``name`` requirement on this class itself.
    """

    _abstract_base = True

    def __init__(
        self,
        pattern: regex.Pattern[str],
        timeout_seconds: float = DEFAULT_REGEX_TIMEOUT_SECONDS,
    ) -> None:
        self._pattern: regex.Pattern[str] = pattern
        self._timeout: float = validate_regex_timeout(timeout_seconds)

    def detect(self, text: str) -> Iterable[Match]:
        for match in self._pattern.finditer(text, timeout=self._timeout):
            yield Match(
                detector=self.name,
                start=match.start(),
                end=match.end(),
                value=match.group(),
            )

    def with_timeout(self, timeout_seconds: float) -> "RegexDetector":
        """Return a shallow copy of this detector with a different timeout."""
        clone = copy.copy(self)
        clone._timeout = validate_regex_timeout(timeout_seconds)
        return clone
