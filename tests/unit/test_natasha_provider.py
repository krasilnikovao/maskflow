from types import SimpleNamespace

import pytest
from pytest import MonkeyPatch

from maskflow.nlp.providers import natasha as natasha_provider_module
from maskflow.nlp.providers.natasha import NatashaProvider


class FakeSpan:
    def __init__(self, start: int, stop: int, span_type: str) -> None:
        self.start = start
        self.stop = stop
        self.type = span_type

    def normalize(self, _morph_vocab: object) -> None:
        return None


class FakeDoc:
    def __init__(self, text: str) -> None:
        self.text = text
        self.spans: list[FakeSpan] = []

    def segment(self, _segmenter: object) -> None:
        return None

    def tag_ner(self, _ner_tagger: object) -> None:
        self.spans = [
            FakeSpan(
                self.text.index("Иван Петров"),
                self.text.index("Иван Петров") + len("Иван Петров"),
                "PER",
            ),
            FakeSpan(
                self.text.index("Москва"),
                self.text.index("Москва") + len("Москва"),
                "LOC",
            ),
        ]


def test_natasha_provider_converts_spans_to_candidates(
    monkeypatch: MonkeyPatch,
) -> None:
    fake_module = SimpleNamespace(
        Segmenter=lambda: object(),
        MorphVocab=lambda: object(),
        NewsEmbedding=lambda: object(),
        NewsNERTagger=lambda _embedding: object(),
        Doc=FakeDoc,
    )
    monkeypatch.setattr(
        natasha_provider_module,
        "import_module",
        lambda _name: fake_module,
    )

    provider = NatashaProvider()

    candidates = list(provider.detect("Клиент Иван Петров живет в Москва"))

    assert [candidate.entity_type for candidate in candidates] == [
        "person",
        "location",
    ]
    assert candidates[0].value == "Иван Петров"
    assert candidates[0].source == "natasha"
    assert candidates[0].priority == 20


def test_natasha_provider_requires_dependency(
    monkeypatch: MonkeyPatch,
) -> None:
    def fail_import(_name: str) -> object:
        raise ImportError

    monkeypatch.setattr(natasha_provider_module, "import_module", fail_import)

    with pytest.raises(RuntimeError, match="natasha is required"):
        list(NatashaProvider().detect("Иван"))
