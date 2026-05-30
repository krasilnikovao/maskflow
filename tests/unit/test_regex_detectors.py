from maskflow.detectors.bank_account import BankAccountDetector
from maskflow.detectors.bik import BikDetector
from maskflow.detectors.email import EmailDetector
from maskflow.detectors.guid import GuidDetector
from maskflow.detectors.inn import InnDetector
from maskflow.detectors.phone import PhoneDetector


def test_email_detector_finds_email() -> None:
    detector = EmailDetector()

    matches = list(detector.detect("Email: admin@example.com"))

    assert len(matches) == 1
    assert matches[0].detector == "email"
    assert matches[0].value == "admin@example.com"


def test_phone_detector_finds_russian_phone() -> None:
    detector = PhoneDetector()

    matches = list(detector.detect("Phone: +7 (999) 123-45-67"))

    assert len(matches) == 1
    assert matches[0].detector == "phone"
    assert matches[0].value == "+7 (999) 123-45-67"


def test_phone_detector_ignores_phone_like_fragment_inside_account() -> None:
    detector = PhoneDetector()

    matches = list(detector.detect("Счет 40802810538320000272"))

    assert matches == []


def test_bank_account_detector_finds_20_digit_account() -> None:
    detector = BankAccountDetector()

    matches = list(detector.detect("Счет 40802810538320000272"))

    assert len(matches) == 1
    assert matches[0].detector == "bank_account"
    assert matches[0].value == "40802810538320000272"


def test_bik_detector_finds_9_digit_bik_starting_with_zero() -> None:
    detector = BikDetector()

    matches = list(detector.detect("БИК 046577964"))

    assert len(matches) == 1
    assert matches[0].detector == "bik"
    assert matches[0].value == "046577964"


def test_inn_detector_finds_10_digit_inn() -> None:
    detector = InnDetector()

    matches = list(detector.detect("ИНН 7707083893"))

    assert len(matches) == 1
    assert matches[0].detector == "inn"
    assert matches[0].value == "7707083893"


def test_inn_detector_finds_12_digit_inn() -> None:
    detector = InnDetector()

    matches = list(detector.detect("ИНН 500100732259"))

    assert len(matches) == 1
    assert matches[0].detector == "inn"
    assert matches[0].value == "500100732259"


def test_guid_detector_finds_guid() -> None:
    detector = GuidDetector()

    matches = list(detector.detect("Ref: 550e8400-e29b-41d4-a716-446655440000"))

    assert len(matches) == 1
    assert matches[0].detector == "guid"
    assert matches[0].value == "550e8400-e29b-41d4-a716-446655440000"
