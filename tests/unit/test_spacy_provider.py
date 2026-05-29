from types import SimpleNamespace

import pytest
from pytest import MonkeyPatch

from maskflow.nlp.providers import spacy as spacy_provider_module
from maskflow.nlp.providers.spacy import SpacyProvider


class FakeEntity:
    def __init__(self, start_char: int, end_char: int, label: str) -> None:
        self.start_char = start_char
        self.end_char = end_char
        self.label_ = label


class FakeDoc:
    def __init__(self, text: str) -> None:
        self.ents = [
            FakeEntity(
                text.index("Иван Петров"),
                text.index("Иван Петров") + len("Иван Петров"),
                "PER",
            ),
            FakeEntity(
                text.index("ООО Ромашка"),
                text.index("ООО Ромашка") + len("ООО Ромашка"),
                "ORG",
            ),
        ]


class FakeSpacyPipeline:
    def __call__(self, text: str) -> FakeDoc:
        return FakeDoc(text)


class FakeSpacyModule:
    loaded_target: str | None = None

    @classmethod
    def load(cls, target: str) -> FakeSpacyPipeline:
        cls.loaded_target = target
        return FakeSpacyPipeline()


def test_spacy_provider_converts_entities_to_candidates(
    monkeypatch: MonkeyPatch,
) -> None:
    fake_module = SimpleNamespace(load=FakeSpacyModule.load)
    monkeypatch.setattr(
        spacy_provider_module,
        "import_module",
        lambda _name: fake_module,
    )

    provider = SpacyProvider(
        model_name="ru_core_news_lg",
        model_path="custom_model",
        auto_download=False,
        batch_size=16,
    )

    candidates = list(provider.detect("Клиент Иван Петров работает в ООО Ромашка"))

    assert FakeSpacyModule.loaded_target == "custom_model"
    assert [candidate.entity_type for candidate in candidates] == [
        "person",
        "organization",
    ]
    assert candidates[0].value == "Иван Петров"
    assert candidates[0].source == "spacy"
    assert candidates[0].priority == 30


def test_spacy_provider_uses_model_name_when_path_is_not_set(
    monkeypatch: MonkeyPatch,
) -> None:
    fake_module = SimpleNamespace(load=FakeSpacyModule.load)
    monkeypatch.setattr(
        spacy_provider_module,
        "import_module",
        lambda _name: fake_module,
    )

    provider = SpacyProvider(
        model_name="ru_core_news_lg",
        model_path=None,
        auto_download=False,
        batch_size=16,
    )

    list(provider.detect("Клиент Иван Петров работает в ООО Ромашка"))

    assert FakeSpacyModule.loaded_target == "ru_core_news_lg"


def test_spacy_provider_requires_dependency(
    monkeypatch: MonkeyPatch,
) -> None:
    def fail_import(_name: str) -> object:
        raise ImportError

    monkeypatch.setattr(spacy_provider_module, "import_module", fail_import)

    provider = SpacyProvider(
        model_name="ru_core_news_lg",
        model_path=None,
        auto_download=False,
        batch_size=16,
    )

    with pytest.raises(RuntimeError, match="spaCy is required"):
        list(provider.detect("Иван"))
