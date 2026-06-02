from typing import cast

from maskflow.detectors.nlp import NlpEntityDetector
from maskflow.nlp.models import ResolvedEntity
from maskflow.nlp.pipeline import NlpPipeline


class FakePipeline:
    def detect(self, text: str) -> list[ResolvedEntity]:
        person = "Иван Петров"
        multiline = "ООО Ромашка\nПлательщикИНН"
        equals = "Ключ=Значение"
        partial_code = "ORG"

        return [
            ResolvedEntity(
                entity_type="person",
                start=text.index(person),
                end=text.index(person) + len(person),
                value=person,
                sources=("gliner",),
                confidence=0.9,
            ),
            ResolvedEntity(
                entity_type="organization",
                start=text.index(multiline),
                end=text.index(multiline) + len(multiline),
                value=multiline,
                sources=("gliner",),
                confidence=0.9,
            ),
            ResolvedEntity(
                entity_type="location",
                start=text.index(equals),
                end=text.index(equals) + len(equals),
                value=equals,
                sources=("gliner",),
                confidence=0.9,
            ),
            ResolvedEntity(
                entity_type="organization",
                start=text.index(partial_code),
                end=text.index(partial_code) + len(partial_code),
                value=partial_code,
                sources=("gliner",),
                confidence=0.9,
            ),
        ]


def test_nlp_detector_filters_unsafe_spans() -> None:
    detector = NlpEntityDetector(cast(NlpPipeline, FakePipeline()))
    text = "\n".join(
        [
            "Контакт: Иван Петров",
            "ООО Ромашка\nПлательщикИНН",
            "Ключ=Значение",
            "Договор №ABCORG0006",
        ],
    )

    matches = list(detector.detect(text))

    assert len(matches) == 1
    assert matches[0].detector == "person"
    assert matches[0].value == "Иван Петров"
