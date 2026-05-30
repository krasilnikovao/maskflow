from typing import Any, cast

from maskflow.detectors.nlp import NlpEntityDetector
from maskflow.nlp.models import ResolvedEntity
from maskflow.nlp.pipeline import NlpPipeline


class FakePipeline:
    def detect(self, _text: str) -> list[ResolvedEntity]:
        return [
            ResolvedEntity(
                entity_type="person",
                start=0,
                end=11,
                value="Иван Петров",
                sources=("gliner",),
                confidence=0.9,
            ),
            ResolvedEntity(
                entity_type="organization",
                start=12,
                end=40,
                value="ООО Ромашка\nПлательщикИНН",
                sources=("gliner",),
                confidence=0.9,
            ),
            ResolvedEntity(
                entity_type="location",
                start=41,
                end=55,
                value="Ключ=Значение",
                sources=("gliner",),
                confidence=0.9,
            ),
        ]


def test_nlp_detector_filters_multiline_and_equals_spans() -> None:
    detector = NlpEntityDetector(cast(NlpPipeline, FakePipeline()))

    matches = list(detector.detect(cast(Any, "")))

    assert len(matches) == 1
    assert matches[0].detector == "person"
    assert matches[0].value == "Иван Петров"
