from collections.abc import Iterable

from maskflow.core.engine import MaskingEngine
from maskflow.core.interfaces import BaseDetector, BaseMasker
from maskflow.core.types import Match
from maskflow.detectors.bank_account import BankAccountDetector
from maskflow.detectors.bik import BikDetector
from maskflow.detectors.document_code import DocumentCodeDetector
from maskflow.detectors.inn import InnDetector
from maskflow.detectors.kpp import KppDetector
from maskflow.detectors.phone import PhoneDetector


class PrefixMasker(BaseMasker):
    name = "prefix"

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def mask(self, value: str) -> str:
        return f"{self.prefix}_TOKEN"


class KeyNameDetector(BaseDetector):
    name = "person"

    def detect(self, text: str) -> Iterable[Match]:
        value = "ПлательщикИНН"
        start = text.find(value)
        if start == -1:
            return

        yield Match(
            detector=self.name,
            start=start,
            end=start + len(value),
            value=value,
        )


def test_statement_like_text_masks_values_without_masking_keys() -> None:
    engine = MaskingEngine(
        detectors=[
            KeyNameDetector(),
            PhoneDetector(),
            BankAccountDetector(),
            BikDetector(),
            DocumentCodeDetector(),
            KppDetector(),
            InnDetector(),
        ],
        maskers={
            "person": PrefixMasker("PERSON"),
            "phone": PrefixMasker("PHONE"),
            "bank_account": PrefixMasker("BANK_ACCOUNT"),
            "bik": PrefixMasker("BIK"),
            "document_code": PrefixMasker("CODE"),
            "kpp": PrefixMasker("KPP"),
            "inn": PrefixMasker("INN"),
        },
    )
    source = "\n".join(
        [
            "ПлательщикИНН=7707083893",
            "ПлательщикБИК=046577964",
            "ПлательщикКПП=773401001",
            "ПлательщикСчет=40802810538320000272",
            "Код=ЗК2603ИП260208340004",
            "Договор=№ABCORG0006",
        ],
    )

    masked = engine.process_text(source)

    assert masked == "\n".join(
        [
            "ПлательщикИНН=INN_TOKEN",
            "ПлательщикБИК=BIK_TOKEN",
            "ПлательщикКПП=KPP_TOKEN",
            "ПлательщикСчет=BANK_ACCOUNT_TOKEN",
            "Код=CODE_TOKEN",
            "Договор=№CODE_TOKEN",
        ],
    )
    assert "PHONE_TOKEN" not in masked
    assert "260208340004" not in masked
    assert "0006" not in masked
