from collections.abc import Iterable

from maskflow.core.interfaces import BaseDetector
from maskflow.core.types import Match
from maskflow.nlp.pipeline import NlpPipeline


class NlpEntityDetector(BaseDetector):
    """Adapter that exposes the NLP subsystem as a MaskFlow detector."""

    name = "nlp"

    def __init__(self, pipeline: NlpPipeline) -> None:
        self.pipeline = pipeline

    def detect(self, text: str) -> Iterable[Match]:
        for entity in self.pipeline.detect(text):
            if not _is_safe_nlp_span(entity.value):
                continue

            yield Match(
                detector=entity.entity_type,
                start=entity.start,
                end=entity.end,
                value=entity.value,
            )


def _is_safe_nlp_span(value: str) -> bool:
    if not value or len(value) > 160:
        return False

    if "\n" in value or "\r" in value or "=" in value:
        return False

    return True
