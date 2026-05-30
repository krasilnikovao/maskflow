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


class BankAccountDetector(BaseDetector):
    name = "bank_account"

    def detect(self, text: str) -> Iterable[Match]:
        value = "40802810538320000272"
        start = text.index(value)
        yield Match(
            detector=self.name,
            start=start,
            end=start + len(value),
            value=value,
        )


class PhoneLikeDetector(BaseDetector):
    name = "phone"

    def detect(self, text: str) -> Iterable[Match]:
        value = "81053832000"
        start = text.index(value)
        yield Match(
            detector=self.name,
            start=start,
            end=start + len(value),
            value=value,
        )


class KeyDetector(BaseDetector):
    name = "person"

    def detect(self, text: str) -> Iterable[Match]:
        value = "ПлательщикИНН"
        start = text.index(value)
        yield Match(
            detector=self.name,
            start=start,
            end=start + len(value),
            value=value,
        )


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


def test_engine_prefers_bank_account_over_phone_overlap() -> None:
    engine = MaskingEngine(
        detectors=[
            PhoneLikeDetector(),
            BankAccountDetector(),
        ],
        maskers={
            "phone": StaticMasker(),
            "bank_account": StaticMasker(),
        },
    )

    result = engine.process_text("Счет 40802810538320000272")

    assert result == "Счет [MASKED]"


def test_engine_does_not_mask_key_part_before_equals() -> None:
    engine = MaskingEngine(
        detectors=[KeyDetector()],
        maskers={"person": StaticMasker()},
    )

    result = engine.process_text("ПлательщикИНН=723008877760")

    assert result == "ПлательщикИНН=723008877760"


def test_engine_does_not_mask_key_with_space_before_equals() -> None:
    """Пробел между ключом и '=' тоже фильтруется."""
    engine = MaskingEngine(
        detectors=[KeyDetector()],
        maskers={"person": StaticMasker()},
    )

    result = engine.process_text("ПлательщикИНН =723008877760")

    assert result == "ПлательщикИНН =723008877760"


def test_engine_masks_value_when_unrelated_equals_on_same_line() -> None:
    """Случайный '=' на строке не должен подавлять матч, стоящий до него."""
    engine = MaskingEngine(
        detectors=[KeyDetector()],
        maskers={"person": StaticMasker()},
    )

    # "ПлательщикИНН" встречается в тексте ДО знака '=', но '=' не следует
    # непосредственно за матчем — это не ключ, маска должна применяться.
    result = engine.process_text("ПлательщикИНН и итого = 42")

    assert result == "[MASKED] и итого = 42"
