from collections.abc import Iterable

from maskflow.core.engine import MaskingEngine
from maskflow.core.interfaces import BaseDetector, BaseMasker
from maskflow.core.types import Match


class LongDetector(BaseDetector):
    name = "long"

    def detect(self, text: str) -> Iterable[Match]:
        yield Match(
            detector=self.name,
            start=0,
            end=10,
            value=text[0:10],
        )


class ShortDetector(BaseDetector):
    name = "short"

    def detect(self, text: str) -> Iterable[Match]:
        yield Match(
            detector=self.name,
            start=2,
            end=5,
            value=text[2:5],
        )


class StaticMasker(BaseMasker):
    name = "static"

    def mask(self, value: str) -> str:
        return "[MASKED]"


def test_engine_prefers_longer_match_on_overlap() -> None:
    engine = MaskingEngine(
        detectors=[
            ShortDetector(),
            LongDetector(),
        ],
        maskers={
            "short": StaticMasker(),
            "long": StaticMasker(),
        },
    )

    result = engine.process_text("0123456789ABC")

    assert result == "[MASKED]ABC"
