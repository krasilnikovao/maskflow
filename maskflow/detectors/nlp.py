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
            yield Match(
                detector=entity.entity_type,
                start=entity.start,
                end=entity.end,
                value=entity.value,
            )
